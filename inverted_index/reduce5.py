#!/usr/bin/env python3
import sys
import itertools

def reduce5(group):
    for line in group:
        words = line.split()
        end = ''

        if len(words) > 1:
            end = ' '.join(words[1:])

        print(f"{end}")


def keyfunc(line):
    return line.partition('\t')[0]    


def main():
    for _, group in itertools.groupby(sys.stdin, keyfunc):
        reduce5(group)


if __name__ == "__main__":
    main()