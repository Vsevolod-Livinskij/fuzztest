#!/bin/bash -e
# Args: FUZZTEST_REPO FUZZTEST_VERSION

if [[ -z "${FUZZTEST_HOME}" ]]; then
    echo "Error! Environmental variable for FUZZTEST_HOME is not set!"
    exit 127
fi

FUZZTEST_REPO=$1
FUZZTEST_VERSION=$2

if [[ -z "${FUZZTEST_REPO}" ]] || [[ -z "${FUZZTEST_VERSION}" ]]; then
    echo "Error! Parameters for FUZZTEST repository are incorrect"
    exit 127
fi

# Get the source code
git clone $FUZZTEST_REPO $FUZZTEST_HOME
cd $FUZZTEST_HOME
git checkout $FUZZTEST_VERSION
echo $FUZZTEST_REPO:$FUZZTEST_VERSION > $FUZZTEST_HOME/fuzztest_rev.txt
git log --format="%H" -n 1 >> $FUZZTEST_HOME/fuzztest_rev.txt

# Compile
CENTIPEDE_SRC=$FUZZTEST_HOME/centipede
BIN_DIR=$FUZZTEST_HOME/bazel-bin/centipede
bazel build -c opt centipede:all
bazel build -c opt centipede/my_fuzz_example:all
