#!/bin/bash -e
# Args: LLVM_REPO LLVM_VERSION

if [[ -z "${LLVM_HOME}" ]]; then
    echo "Error! Environmental variable for LLVM_HOME is not set!"
    exit 127
fi

if [[ -z "${FUZZTEST_HOME}" ]]; then
    echo "Error! Environmental variable for FUZZTEST_HOME is not set!"
    exit 127
fi

LLVM_REPO=$1
LLVM_VERSION=$2

if [[ -z "${LLVM_REPO}" ]] || [[ -z "${LLVM_VERSION}" ]]; then
    echo "Error! Parameters for LLVM repository are incorrect"
    exit 127
fi

# Get the source code
mkdir -p $LLVM_HOME
cd $LLVM_HOME
git clone "$LLVM_REPO" "llvm_src" 2> /dev/null || (cd "llvm_src" ; git fetch "$LLVM_REPO" && git checkout origin/main)
mkdir centipede_build_$LLVM_VERSION centipede_bin_$LLVM_VERSION
cd $LLVM_HOME/llvm_src
git checkout $LLVM_VERSION
echo $LLVM_REPO:$LLVM_VERSION > $LLVM_HOME/llvm_rev.txt
git log --format="%H" -n 1 >> $LLVM_HOME/llvm_rev.txt

# This is a horrible hack, but we need to ensure that libcentipede_runner_no_main.a is always passed to the linker as the last argument
echo "#!/bin/bash" > $LLVM_HOME/clang-wrapper
echo "clang \"\$@\" -lstdc++ $FUZZTEST_HOME/bazel-bin/centipede/libcentipede_runner_no_main.a" >> $LLVM_HOME/clang-wrapper
chmod +x $LLVM_HOME/clang-wrapper

echo "#!/bin/bash" > $LLVM_HOME/clang++-wrapper
echo "clang++ \"\$@\" -lstdc++ $FUZZTEST_HOME/bazel-bin/centipede/libcentipede_runner_no_main.a" >> $LLVM_HOME/clang++-wrapper
chmod +x $LLVM_HOME/clang++-wrapper

# Pre-compilation steps
cd $LLVM_HOME/centipede_build_$LLVM_VERSION
CC=$LLVM_HOME/clang-wrapper \
CXX=$LLVM_HOME/clang++-wrapper \
CXXFLAGS="-DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION -fno-builtin -fsanitize-coverage=trace-pc-guard,pc-table,trace-cmp,control-flow  -gline-tables-only -fsanitize-coverage-allowlist=/allowlist.txt" \
cmake -G "Ninja" \
    -DCMAKE_INSTALL_PREFIX=$LLVM_HOME/centipede_bin_$LLVM_VERSION \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLVM_ENABLE_ASSERTIONS=ON \
    -DLLVM_INSTALL_UTILS=ON \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    -DLLVM_TARGETS_TO_BUILD=X86 \
    -DLLVM_ENABLE_PROJECTS="clang" \
    $LLVM_HOME/llvm_src/llvm

# Compile
ninja clang

# Cleanup
#rm -rf $LLVM_HOME/centipede_build_$LLVM_VERSION $LLVM_HOME/llvm_src

