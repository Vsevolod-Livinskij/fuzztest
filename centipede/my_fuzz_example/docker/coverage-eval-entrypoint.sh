#!/bin/bash

num_iterations=$1
testing_time=$2

# Launch the process killer
COMPILER_TIMEOUT=300
python3 $FUZZTEST_HOME/centipede/my_fuzz_example/eval_scripts/hang_process_killer.py "$LLVM_HOME/centipede_build_llvmorg-17.0.6/bin/clang++" $COMPILER_TIMEOUT > /dev/null 2>&1 &

cd $FUZZTEST_HOME/centipede/my_fuzz_example/eval_scripts

for i in $(seq 1 $num_iterations)
do
    echo "Iteration $i"
    ./evaluate_coverage.sh $testing_time
done
