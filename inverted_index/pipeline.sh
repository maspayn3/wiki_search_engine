#!/bin/bash

BASE_HDFS_PATH="/user/maspayne"

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

# MUST ssh to localhost before anything
# $ sudo service ssh start
# $ ssh localhost

# start-all.sh
# jps - checks to see if processes are running

# setup local host first
# ???

# start-all.sh

# # rid of previous output directories
rm -rf output output[0-9] || true

hdfs dfs -rm -r /user/maspayne/inverted_index/output[0-5]

hdfs dfs -put -f ./input/data.csv /user/maspayne/input/

mapred streaming -files map0.py,reduce0.py\
    -input /${BASE_HDFS_PATH}/input \
    -output ${BASE_HDFS_PATH}/inverted_index/output0 \
    -mapper ./map0.py \
    -reducer ./reduce0.py

mapred streaming -files map1.py,reduce1.py,stopwords.txt\
    -input ${BASE_HDFS_PATH}/input \
    -output ${BASE_HDFS_PATH}/inverted_index/output1 \
    -mapper ./map1.py \
    -reducer ./reduce1.py

mapred streaming -files map2.py,reduce2.py,doc_count.txt\
    -input ${BASE_HDFS_PATH}/inverted_index/output1 \
    -output ${BASE_HDFS_PATH}/inverted_index/output2 \
    -mapper ./map2.py \
    -reducer ./reduce2.py

mapred streaming -files map3.py,reduce3.py\
    -input ${BASE_HDFS_PATH}/inverted_index/output2 \
    -output ${BASE_HDFS_PATH}/inverted_index/output3 \
    -mapper ./map3.py \
    -reducer ./reduce3.py

mapred streaming -files map4.py,reduce4.py\
    -input ${BASE_HDFS_PATH}/inverted_index/output3 \
    -output ${BASE_HDFS_PATH}/inverted_index/output4 \
    -mapper ./map4.py \
    -reducer ./reduce4.py

mapred streaming -files map5.py,reduce5.py\
    -D mapreduce.job.reduces=3 \
    -input ${BASE_HDFS_PATH}/inverted_index/output4 \
    -output ${BASE_HDFS_PATH}/inverted_index/output5 \
    -mapper ./map5.py \
    -reducer ./reduce5.py


    # Hadoop notes
    # -files puts local files into a distributed cache so they are available to 
    # all task nodes
    # 