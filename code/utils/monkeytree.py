#!/usr/bin/env python3
# -*- coding: utf-8 -*-



# Ugly test hack
if __name__ == '__main__':
  import sys
  sys.path.append('./')
  sys.path.append('code/')



from collections import deque
from operator import itemgetter, attrgetter

import inspect
from pickle import Pickler, Unpickler
import gzip, bz2


class NoSuchNode(Exception):
  "No such node is in the tree"


# Couple of static itemgetter functions
MONKEY_IG0    = itemgetter(0)
MONKEY_IG1    = itemgetter(1)



class MonkeyNode(object):
  
  '''
  You are in a maze of twisty probabilistic recursive monkey nodes.  How the
  fuck did you get here?
  
  While working the tree this makes is not optimal.  In particular the last (& 
  most numerous) level could be eliminated if we stored its count in the
  parent's node_row tuples.
  '''
  
  def __init__(self):
    super(MonkeyNode,self).__init__()
    self.children       = {}  # event => (count, child_node)
    self.probabilities  = {}  # event => probability
  
  
  def __len__(self):
    return len(self.children)
  
  
  def depth(self):
    "Calculate the maximum depth of this tree"
    return max([0]+[c.depth() for c in self._childNodes()]) + 1
  
    
  def _childNodes(self):
    "All non-null child nodes"
    return filter(None, [MONKEY_IG1(v) for v in self.children.values()])
  
    
  def update(self, s):
    '''
    Recursively update the tree with information contained within sequence `s`,
    which must be a collections.deque.  `s` will be destroyed in the process.
    '''
    
    # Get the representation of this node, or a new one
    our_event = s.popleft()
    try:
      count, child_node         = self.children[our_event]
      self.children[our_event]  = (count+1, child_node)
      self.probabilities        = {}  # becomes invalid
    except KeyError:
      child_node = MonkeyNode() if len(s) else None
      self.children[our_event] = (1, child_node)
    
    # Recurse into it to add the next value in the sequence
    if len(s):
      child_node.update(s)
    
    # Update our probability distribution
    total = sum(map(MONKEY_IG0, self.children.values()))
    for k, v in self.children.items():
      count, child_node = v
      self.probabilities[k] = count / total
  
  
  def predictEndNode(self, s, closest=False):
    '''
    Return the end node that the sequence takes us to
    '''
    # Get the representation of this node
    our_event = s.popleft()
    try:
      count, child_node = self.children[our_event]
    except KeyError:
      if closest:
        child_node = self.sortPredictions()[0][2]
      else:
        raise NoSuchNode()
    
    # Are we at the end of the sequence?  Return our prediction
    if not len(s):
      if child_node:
        return child_node
      else:
        raise NoSuchNode()
    
    # More left to go?
    return child_node.predictEndNode(s, closest)


  def predict(self, s, closest=False):
    '''
    Given sequence s, try to predict what happens next.  `s` must be a
    collections.deque at least one shorter than the depth of the tree. and will
    be destroyed in the operation.
    '''
    child_node = self.predictEndNode(s, closest)
    return child_node.sortPredictions()[0][0]
  
  
  def cumulativeProbability(self, funk):
    '''
    Return the cumulative probability of all potential outcomes whose event is
    selected by `funk`.
    '''
    return sum([v for k, v in self.probabilities.items() if funk(k)])
  
    
  def checkCounts(self):
    '''
    Check the integrity of the tree by recursively comparing each node's event
    count to the sum of its children's.
    '''
    my_total    = sum(map(MONKEY_IG0, self.children.values()))
    child_total = sum( map(MONKEY_IG0, self.children.values()) )
    if child_total != my_total:
      raise ValueError("Child count did not match my own")
    for child in self._childNodes():
      child.checkCounts()
  
  
  def checkProbabilityMass(self):
    '''
    Check probabilities always add up to 1
    '''
    total = sum(self.probabilities.values())
    if not 0.999999 < total < 1.000001:       # Allow for fp errors
      raise ValueError("Total prob mass should be 1, actually %f" % total)
    for child in self._childNodes():
      child.checkProbabilityMass()
  
  
  def checkCoverage(self, events):
    '''
    For an exhaustive list of `events`, return a tuple of (covered, absent)
    for all nodes of the tree.  This is a metric for how `complete` our
    probability tree is.
    '''
    covered, absent = self._coverageTotals(events)
    return covered / (covered+absent)
  
  
  def _coverageTotals(self, events):
    "Recursive helper function for checkCoverage()"
    covered = sum([1 if e in self.children else 0 for e in events])
    absent  = len(events) - covered
    
    for child in self._childNodes():
      child_covered, child_absent = child._coverageTotals(events)
      covered += child_covered
      absent  += child_absent
    
    return (covered, absent)
  
  
  def sortPredictions(self):
    '''
    Return all this node's predictions in order of decreasing likelihood. 
    Predictions are in the form of tuples of (event, probability, child).
    '''
    triplets = [(k, p, self.children[k][1]) for k, p in self.probabilities.items()]
    return sorted(triplets, key=MONKEY_IG1, reverse=True)
  
    
  def dump(self, indent=0, recurse=True):
    '''
    For debugging: recursively dump our contents
    '''
    for k, probability in self.probabilities.items():
      child = self.children[k][1]
      print("%s %-.3f prob:%.3f" % (
        (' ' * indent), k, probability
      ))
      if recurse and child:
        child.dump(indent+2)
  
  



class MonkeyTree(object):
  
  '''
  Wrapper for a tree of monkeynodes with added load and save methods.  Proxies
  methods directly from the tree's root node so can be addressed in the same
  way.
  '''
  
  def __init__(self, root=None):
    super(MonkeyTree,self).__init__()
    self.root = root if root else MonkeyNode()
    
    # Monkeypatch (ha!) methods into place from the root node we are wrapping.
    # This is 471% faster than __getattr__ for each method.  See
    # https://stackoverflow.com/questions/26091833/proxy-object-in-python
    for name, value in inspect.getmembers(self.root, callable):
      if not hasattr(self, name):
          setattr(self, name, value)
  
  
  def __str__(self):
    return "<%s depth:%d>" % (
      self.__class__.__name__,
      self.root.depth()
    )
  
  
  def __len__(self):
    # Hmmm this evades the monkeypatch
    return len(self.root)
  
  
  #
  # Tree loading & saving
  #
  def save(self, filename):
    '''
    Save this monkey tree to disk at the specified filename
    '''
    if filename.endswith('.gz'):
      fp = gzip.GzipFile(filename, 'w')
    elif filename.endswith('.bz2'):
      fp = bz2.BZ2File(filename, 'w')
    else:
      fp = open(filename, 'wb')
    p = Pickler(fp)
    p.dump(self.root)
    fp.close()
  
  
  @staticmethod
  def load(filename):
    '''
    Load a saved monkeytree from disk
    '''
    if filename.endswith('.gz'):
      fp = gzip.GzipFile(filename, 'r')
    elif filename.endswith('.bz2'):
      fp = bz2.BZ2File(filename, 'r')
    else:
      fp = open(filename, 'rb')
    u = Unpickler(fp)
    return MonkeyTree(root=u.load())




if __name__ == '__main__':
  
  import random
  
  # root = MonkeyNode()
  # sequence = deque( [1,4] + [random.randint(1,10) for i in range(0,6)] )
  # root.update(sequence)
  # sequence = deque( [1,4] + [random.randint(1,10) for i in range(0,6)] )
  # root.update(sequence)
  # sequence = deque( [1,7] + [random.randint(1,10) for i in range(0,6)] )
  # root.update(sequence)
  # sequence = deque( [1,4,1,1,1,1,1] )
  # root.update(sequence)
  # 
  # root.checkCounts()
  # root.dump()
  
  # mt = MonkeyTree()
  # sequence = deque( [1,4] + [random.randint(1,10) for i in range(0,6)] )
  # mt.update(sequence)
  # mt.save('/tmp/monkeytree.pkl')
  
  mt = MonkeyTree.load('/tmp/monkeytree.pkl')
  print("loaded %s" % mt)
  
