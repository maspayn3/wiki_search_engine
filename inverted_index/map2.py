#!/usr/bin/env python3

import sys

for line in sys.stdin:
    word, doc_id, count = line.strip().split()
    print(f"{word}\t{doc_id} {count}")
