#!/usr/bin/env python3
import sys
import util

def reduce0():
    """Prints the number of documents."""
    count = sum(1 for _ in sys.stdin)
    print(f"{count}")

    return count


def main():
    count = reduce0()

    with open('doc_count.txt', mode='w', encoding='utf-8') as file:
        file.write(str(count))

if __name__ == "__main__":
    main()