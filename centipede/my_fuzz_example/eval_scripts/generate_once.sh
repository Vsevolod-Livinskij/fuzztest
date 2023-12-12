#!/bin/bash

tid=$1
seed=$2

mkdir -p $RANDOM_CORPUS
$YARPGEN_HOME/build/yarpgen -c $RANDOM_CORPUS/$tid_$seed --single-file=true
