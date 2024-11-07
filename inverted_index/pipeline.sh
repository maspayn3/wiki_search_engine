#!/bin/bash

# stop on errors
# set -Eeuo pipefail

# run pipeline via bash commands (pipes)
# cat ./input/data.csv | ./map0.py | sort | ./reduce0.py
# cat ./input/data.csv | ./map1.py | sort | ./reduce1.py | ./map2.py | sort | ./reduce2.py | \
#                        ./map3.py | sort | ./reduce3.py | ./map4.py | sort | ./reduce4.py | \
#                        ./map5.py | sort | ./reduce5.py

# # Hadoop pipeline program -> chaining MapReduce jobs
# # jar index/hadoop/hadoop-streaming-{VERSION}.jar
# # - input <directory>       # input directory
# # - output <directory>      # output directory
# # - mapper <exec_name>      # mapper executable
# # - reducer <exec_name>     # reducer executable

#HADOOP SETUP COMMANDS

# setup local host first
# ???

# start-all.sh

# # rid of previous output directories
rm -rf output output[0-9] || true

hdfs dfs -rm -r /inverted_index/output[0-5]

mapred streaming -files map0.py,reduce0.py\
    -input /input \
    -output /inverted_index/output0 \
    -mapper ./map0.py \
    -reducer ./reduce0.py

mapred streaming -files map1.py,reduce1.py,stopwords.txt\
    -input /input \
    -output /inverted_index/output1 \
    -mapper ./map1.py \
    -reducer ./reduce1.py

mapred streaming -files map2.py,reduce2.py,doc_count.txt\
    -input /inverted_index/output1 \
    -output /inverted_index/output2 \
    -mapper ./map2.py \
    -reducer ./reduce2.py

mapred streaming -files map3.py,reduce3.py\
    -input /inverted_index/output2 \
    -output /inverted_index/output3 \
    -mapper ./map3.py \
    -reducer ./reduce3.py

mapred streaming -files map4.py,reduce4.py\
    -input /inverted_index/output3 \
    -output /inverted_index/output4 \
    -mapper ./map4.py \
    -reducer ./reduce4.py

mapred streaming -files map5.py,reduce5.py\
    -D mapreduce.job.reduces=3 \
    -input /inverted_index/output4 \
    -output /inverted_index/output5 \
    -mapper ./map5.py \
    -reducer ./reduce5.py