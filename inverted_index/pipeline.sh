#!/bin/bash

# stop on errors
set -Eeuo pipefail

# Hadoop pipeline program -> chaining MapReduce jobs
# jar index/hadoop/hadoop-streaming-{VERSION}.jar
# - input <directory>       # input directory
# - output <directory>      # output directory
# - mapper <exec_name>      # mapper executable
# - reducer <exec_name>     # reducer executable

# rid of previous output directories
rm -rf output output[0-9]

mapred streaming \
    -input input \
    -output ouput 0 \
    -mapper ./map0.py \
    -reducer ./reduce0.py