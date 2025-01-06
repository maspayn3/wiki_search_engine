#!/usr/bin/env python3
import sys
import itertools
import logging
import os
logging.basicConfig(
    filename='index_performance.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)
logging.info(f"Starting {os.path.basename(__file__)}")

def reduce1(group):
    """Reduce input one {WORD DOC_ID} group at a time"""
    word_count = 0
    for line in group:
        word, doc_id, count = line.strip().split()
        word_count += int(count)

    print(f"{word} {doc_id}\t{word_count}")

def keyfunc(line):
    return line.partition('\t')[0]

def main():
    # user itertools.groupby to group input by {WORD DOC_ID} key
    for _, group in itertools.groupby(sys.stdin, keyfunc):
        reduce1(group)

if __name__ == "__main__":
    main()
    # At the end of the main processing
    logging.info(f"Completed {os.path.basename(__file__)}")