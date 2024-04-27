#!/usr/bin/env python3
import sys
import itertools


def reduce3(group):
    group = list(group)
    norm = 0
    for line in group:
        _, _, _, _, norm_factor = line.strip().split()
        norm += float(norm_factor)
    
    for line in group:
        doc_id, word, idf, word_count = line.strip().split()
        file = int(doc_id) % 3
        print(f"{file} {word}\t {doc_id} {idf} {word_count} {norm}")


def key(line):
    return line.partition('\t')[0]


def main():
    for _, group in itertools.groupby(sys.stdin, key):
        reduce3(group)


if __name__ == "__main__":
    main()