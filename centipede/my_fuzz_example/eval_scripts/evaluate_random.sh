#!/bin/bash

# Testing time in hours
num_tests=$1

# GLOBALS
# TODO: MOVE ME
export TIMEOUT=300
export TARGET_CLANG="$LLVM_HOME/centipede_build_llvmorg-17.0.6/bin/clang++"
export RANDOM_CENTIPEDE_WD=$RESULT_DIR/random-centipede-wd
export RANDOM_CORPUS=$RESULT_DIR/random-corpus
export RANDOM_RESULT_WD=$RESULT_DIR/random-result-wd
export RANDOM_RESULT_FILE=$RESULT_DIR/random-result.txt

mkdir -p $RANDOM_CENTIPEDE_WD
mkdir -p $RANDOM_CORPUS
mkdir -p $RANDOM_RESULT_WD
touch $RANDOM_RESULT_FILE

# Clean up old corpus
rm -rf ${RANDOM_CORPUS:?}/*

# Generate tests to populate random corpus
# Ohm can process 12.5k tests per minute.
#ohm_throughput=12500
#ohm_throughput=17
# Number of tests to generate
#num_tests=$(($testing_time * 60 * $ohm_throughput))
jobs_num=$(nproc)
#jobs_num=5
echo "Starting random corpus generation"
date
python3 parallel_generate.py --seeds-num $num_tests -j $jobs_num --result-dir $RESULT_DIR
# Seeds updated
# $RANDOM_CORPUS/ with choice sequences
touch $RANDOM_CORPUS/null
echo "Finished random corpus generation"
date


# Process the corpus with centipede
# This will also combine the new corpus with the old one
echo "Processing corpus"
date
$FUZZTEST_HOME/bazel-bin/centipede/my_fuzz_example/main \
    --binary=$TARGET_CLANG \
    --batch_size=1 \
    --mutate_batch_size=1 \
    --rss_limit_mb=0 \
    --address_space_limit_mb=0 \
    --timeout_per_input=$TIMEOUT \
    --timeout_per_batch=$TIMEOUT \
    --max_len=100000 \
    --num_crash_reports=10000 \
    --fork_server=false \
    --num_runs=0 \
    -j $jobs_num \
    --stop_after=24h \
    --corpus_dir=$RANDOM_CORPUS \
    --workdir=$RANDOM_CENTIPEDE_WD/
echo "Finished processing corpus"

# Evaluate the new corpus
# Distill the corpus and save the numbers to a separate file
echo "Starting distillation"
date
$FUZZTEST_HOME/bazel-bin/centipede/my_fuzz_example/main \
   --binary=$TARGET_CLANG \
   --batch_size=1 \
   --mutate_batch_size=1 \
   --rss_limit_mb=0 \
   --address_space_limit_mb=0 \
   --timeout_per_input=$TIMEOUT \
   --timeout_per_batch=$TIMEOUT \
   --max_len=100000 \
   --num_crash_reports=10000 \
   --fork_server=false \
   --num_runs=0 \
   --stop_after=24h \
   --workdir=$RANDOM_CENTIPEDE_WD \
   --distill \
   --total_shards=$jobs_num \
   --num_threads=1 > $RESULT_DIR/random_distill.txt 2>&1
timestamp=$(date '+%F_%H%M')
cp -r $RANDOM_CENTIPEDE_WD $RANDOM_RESULT_WD-$timestamp
date
date >> $RANDOM_RESULT_FILE
tail -n 1 $RESULT_DIR/random_distill.txt >> $RANDOM_RESULT_FILE
echo "Finished distillation"
date
