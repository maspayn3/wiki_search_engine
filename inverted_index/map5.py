#!/usr/bin/env python3
import sys
import os
# At the start of each map/reduce script
import logging
logging.basicConfig(
    filename='index_performance.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.info(f"Starting {os.path.basename(__file__)}")


for line in sys.stdin:
    print(line.strip())

# At the end of the main processing
logging.info(f"Completed {os.path.basename(__file__)}")