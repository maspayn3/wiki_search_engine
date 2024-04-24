import sys
import itertools
import csv

def reduce1(group):
    """Reduce input one {WORD DOC_ID} group at a time"""
    for line in group:
        word, doc_id, count = line.strip().split()
        word_count += int(count)

    print(f"{word} {doc_id}\t{word_count}")

def key(line):
    """Returns tab deliminated key from map job"""
    # input format: WORD DOC_ID \t 1
    return line.partition('\t')[0]

def main():
    # user itertools.groupby to group input by {WORD DOC_ID} key
    for _, group in itertools.groupby(sys.stdin, key):
        reduce1(group)


if __name__ == "__main__":
    main()