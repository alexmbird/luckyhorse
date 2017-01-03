#!/usr/bin/env python3
# -*- coding: utf-8 -*-






def centreText(text, width):
  "Centre a single line of text"
  text = text.strip()
  if len(text) > width:
    return text
  indent = int( (width - len(text)) / 2)
  return (' ' * indent) + text


