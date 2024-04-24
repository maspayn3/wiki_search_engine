#!/usr/bin/env python3

import sys
import csv

csv.field_size_limit(sys.maxsize)
COUNT = 1
for row in csv.reader(sys.stdin):
    print(f"Doc\t{COUNT}")