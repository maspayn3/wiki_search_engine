#!/usr/bin/env python3
import sys
import os

sys.path.append(os.path.dirname(__file__))

def reduce0():
    """Prints the number of documents."""
    try:
        count = sum(1 for _ in sys.stdin)
        print(f"{count}")

        with open("doc_count.txt", "w") as f:
            f.write(str(count))

    except Exception as e:
        sys.stderr.write(f"Error in reducer: {e}\n")
        sys.exit(1)

if __name__ == "__main__":
    reduce0()