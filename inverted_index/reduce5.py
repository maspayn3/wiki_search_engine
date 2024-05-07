#!/usr/bin/env python3
import sys
import itertools
import util


def reduce5(group, file):

    for line in group:
        words = line.split()
        end = ''
        if len(words) > 1:
            end = ' '.join(words[1:])

        file.write(end)
        file.write('\n')
       
        
        


def main():
    with open('output.txt', mode='a', encoding='utf-8') as file:
        for _, group in itertools.groupby(sys.stdin, util.keyfunc):
            reduce5(group, file)


if __name__ == "__main__":
    main()