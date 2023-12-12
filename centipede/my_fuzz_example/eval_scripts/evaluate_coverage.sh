#!/bin/bash

# Testing time in hours
testing_time=$1

# GLOBALS
# TODO: MOVE ME
export TIMEOUT=300
export TARGET_CLANG="$LLVM_HOME/centipede_build_llvmorg-17.0.6/bin/clang++"
export COVERAGE_CENTIPEDE_WD=$RESULT_DIR/coverage-centipede-wd
export COVERAGE_CORPUS=$RESULT_DIR/coverage-corpus
export COVERAGE_RESULT_WD=$RESULT_DIR/coverage-result-wd
export COVERAGE_RESULT_FILE=$RESULT_DIR/coverage-result.txt

mkdir -p $COVERAGE_CENTIPEDE_WD
mkdir -p $COVERAGE_CORPUS
mkdir -p $COVERAGE_RESULT_WD
touch $COVERAGE_RESULT_FILE

# Clean up old corpus and put initial seed
rm -rf ${COVERAGE_CORPUS:?}/*
cp $FUZZTEST_HOME/centipede/my_fuzz_example/eval_scripts/42 $COVERAGE_CORPUS/42
touch $COVERAGE_CORPUS/null

# Cleanup old WD from distilled corpus to avoid loading old files
rm -rf ${COVERAGE_CENTIPEDE_WD:?}/distilled-*
rm -rf ${COVERAGE_CENTIPEDE_WD:?}/clang++*/distilled-features-*

jobs_num=$(nproc)

# Test with centipede
# This will also combine the new corpus with the old one
echo "Started testing"
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
    --num_runs=1000000 \
    -j $jobs_num \
    --stop_after=${testing_time}h \
    --corpus_dir=$COVERAGE_CORPUS \
    --workdir=$COVERAGE_CENTIPEDE_WD/
echo "Finished testing"

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
   --workdir=$COVERAGE_CENTIPEDE_WD \
   --distill \
   --total_shards=$jobs_num \
   --num_threads=1 > $RESULT_DIR/coverage_distill.txt 2>&1
timestamp=$(date '+%F_%H%M')
cp -r $COVERAGE_CENTIPEDE_WD $COVERAGE_RESULT_WD-$timestamp
date
date >> $COVERAGE_RESULT_FILE
tail -n 1 $RESULT_DIR/coverage_distill.txt >> $COVERAGE_RESULT_FILE
echo "Finished distillation"
date
