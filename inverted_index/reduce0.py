#!/usr/bin/env python3
import sys

def reduce0():
    """Prints the number of documents."""
    count = sum(1 for _ in sys.stdin)
    print(f"{count}")


def main():
    reduce0()


if __name__ == "__main__":
    main()