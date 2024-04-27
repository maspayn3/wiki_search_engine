#!/usr/bin/env python3

import sys
import itertools
import math

def reduce2(group):
    """Calculate idf"""

    group = list(group)
    doc_count = len(group)

    temp = 0

    idf = temp /float(doc_count)

    idf = math.log(idf, 10)
    for line in group:
        word, doc_id, count = line.strip().split()
        norm_factor = pow((float(count) * idf), 2)
        print(f"{doc_id}\t{word} {idf} {count} {norm_factor}")

def key(line):
    return line.partition("\t")[0]

def main():
    for _, group in itertools.groupby(sys.stdin, key):
        reduce2(group)

if __name__ == "__main__":
    main()