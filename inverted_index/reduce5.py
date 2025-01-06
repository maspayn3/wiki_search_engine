#!/usr/bin/env python3
import sys
import itertools
import os
import logging

logging.basicConfig(
    filename='index_performance.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.info(f"Starting {os.path.basename(__file__)}")

line_count = 0
group_count = 0

def reduce5(group):
    global line_count
    for line in group:
        # Keep the word at the start of the line
        words = line.split()
        if len(words) >= 2:  # Make sure we have at least word and some data
            word = words[0]  # Keep the word
            rest = ' '.join(words[1:])  # Join the rest of the data
            print(f"{word} {rest}")  # Print word followed by the rest
            line_count += 1
            if line_count % 10000 == 0:
                logging.info(f"reduce5.py: Processed {line_count} lines")

def keyfunc(line):
    return line.partition('\t')[0]

def main():
    global group_count
    for _, group in itertools.groupby(sys.stdin, keyfunc):
        reduce5(group)
        group_count += 1
        if group_count % 1000 == 0:
            logging.info(f"reduce5.py: Processed {group_count} groups")

if __name__ == "__main__":
    try:
        main()
        logging.info(f"Completed {os.path.basename(__file__)} - Processed {line_count} lines in {group_count} groups")
    except Exception as e:
        logging.error(f"Error in {os.path.basename(__file__)}: {str(e)}")
        raise