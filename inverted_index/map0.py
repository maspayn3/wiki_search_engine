#!/usr/bin/env python3

import sys
import csv

csv.field_size_limit(sys.maxsize)
COUNT = 1
with open('../data.csv', mode='r') as file:
    for row in csv.reader(file):
        print(f"Doc\t{COUNT}")