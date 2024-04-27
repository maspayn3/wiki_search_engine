#!/bin/bash



# stop on errors
set -Eeuo pipefail

# run pipeline via bash commands
cat ./input/data.csv | ./map0.py | sort | ./reduce0.py
cat ./input/data.csv | ./map1.py | sort | ./reduce1.py

# # Hadoop pipeline program -> chaining MapReduce jobs
# # jar index/hadoop/hadoop-streaming-{VERSION}.jar
# # - input <directory>       # input directory
# # - output <directory>      # output directory
# # - mapper <exec_name>      # mapper executable
# # - reducer <exec_name>     # reducer executable

# # rid of previous output directories
# rm -rf output output[0-9]

# hdfs dfs -rm -r /user/hadoop/output0

# mapred streaming -files map0.py, reduce0.py\
#     -input input \
#     -output ouput0 \
#     -mapper ./map0.py \
#     -reducer ./reduce0.py
