FROM ubuntu:22.04

ENV TESTING_HOME=/testing

ENV GCC_HOME=$TESTING_HOME/gcc
ARG GCC_REPO=https://gcc.gnu.org/git/gcc.git
ARG GCC_VERSION=master

ENV LLVM_HOME=$TESTING_HOME/llvm
ARG LLVM_REPO=https://github.com/llvm/llvm-project.git
# This is the LLVM version that we use to compile instrumented binary
# The system default isa bit old, so we use a separate one
ARG LLVM_INSTR_VERSION=llvmorg-17.0.6
ARG LLVM_VERSION=main

ENV BINUTILS_HOME=$TESTING_HOME/binutils
ARG BINUTILS_REPO=https://sourceware.org/git/binutils-gdb.git

ARG SDE_REPO=https://downloadmirror.intel.com/751535
ARG SDE_VERSION=sde-external-9.14.0-2022-10-25-lin

# Centipede lives inside fuzztest repo
ENV FUZZTEST_HOME=$TESTING_HOME/fuzztest
#ARG FUZZTEST_REPO=https://github.com/google/fuzztest
#ARG FUZZTEST_VERSION=main
ARG FUZZTEST_REPO=https://github.com/Vsevolod-Livinskij/fuzztest.git
ARG FUZZTEST_VERSION=compiler_fuzzing

ENV YARPGEN_HOME=$TESTING_HOME/yarpgen
#ARG YARPGEN_REPO=https://github.com/intel/yarpgen
#ARG YARPGEN_VERSION=main
ARG YARPGEN_REPO=https://github.com/Vsevolod-Livinskij/yarpgen.git
ARG YARPGEN_VERSION=centipede-eval

ARG USER_AGENT="Mozilla/5.0"

RUN apt-get -y update &&\
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    bison \
    bzip2 \
    cmake \
    clang \
    creduce \
    curl \
    flex \
    gcc \
    gcc-multilib \
    g++ \
    git \
    libgmp-dev \
    libmpfr-dev \
    libssl-dev \
    libz-dev \
    ninja-build \
    python3 \
    texinfo \
    wget \
    xz-utils \
    terminfo \
    valgrind \
    pkg-config \
    libedit-dev \
    &&\
    apt-get install apt-transport-https curl gnupg -y &&\
    curl -fsSL https://bazel.build/bazel-release.pub.gpg | gpg --dearmor >bazel-archive-keyring.gpg &&\
    mv bazel-archive-keyring.gpg /usr/share/keyrings &&\
    echo deb [arch=amd64 signed-by=/usr/share/keyrings/bazel-archive-keyring.gpg] https://storage.googleapis.com/bazel-apt stable jdk1.8 | tee /etc/apt/sources.list.d/bazel.list &&\
    apt-get -y update &&\
    apt-get -y install bazel-6.4.0 &&\
    apt-get install pip -y &&\
    pip install --no-cache-dir --upgrade pip &&\
    pip install --no-cache-dir psutil &&\
    rm -rf /var/lib/apt/lists/*


WORKDIR $TESTING_HOME

# Get SDE
RUN wget -U $USER_AGENT --retry-connrefused --waitretry=5 --read-timeout=20 --timeout=15 -t 5 $SDE_REPO/$SDE_VERSION.tar.xz
RUN tar -xf $SDE_VERSION.tar.xz
ENV PATH=$TESTING_HOME/$SDE_VERSION:$PATH


RUN git clone $FUZZTEST_REPO $FUZZTEST_HOME &&\
    cd $FUZZTEST_HOME &&\
    git checkout $FUZZTEST_VERSION


# Build the LLVM version that we use for instrumentation
RUN $FUZZTEST_HOME/centipede/my_fuzz_example/docker/build_llvm.sh $LLVM_REPO $LLVM_INSTR_VERSION

ENV PATH=$LLVM_HOME/bin_$LLVM_INSTR_VERSION/bin/:$PATH
ENV LD_LIBRARY_PATH=$LLVM_HOME/bin_$LLVM_INSTR_VERSION/lib/:$LD_LIBRARY_PATH


# Builde centipede
RUN $FUZZTEST_HOME/centipede/my_fuzz_example/docker/build_centipede.sh $FUZZTEST_REPO $FUZZTEST_VERSION


# Build instrumented LLVM
# Enable instrumentation for a whole folder and all functions in those files
RUN echo "src:$LLVM_HOME/llvm_src/llvm/*" > /allowlist.txt &&\
    echo "fun:*" >> /allowlist.txt
RUN $FUZZTEST_HOME/centipede/my_fuzz_example/docker/build_llvm_for_centipede.sh $LLVM_REPO $LLVM_VERSION


# Build yarpgen
RUN git clone $YARPGEN_REPO $YARPGEN_HOME &&\
    cd $YARPGEN_HOME &&\
    git checkout $YARPGEN_VERSION &&\
    git submodule update --init --recursive &&\
    $YARPGEN_HOME/scripts/build_yarpgen.sh
ENV PATH=$YARPGEN_HOME/build/:$PATH


ARG RESULT_DIR
ENV RESULT_DIR=${RESULT_DIR:-$TESTING_HOME/result}
VOLUME $RESULT_DIR

ENTRYPOINT ["/testing/fuzztest/centipede/my_fuzz_example/docker/random-eval-entrypoint.sh"]
# Ohm does 19200 tests per minute. We want to use 60 machines to approximate 5 days of testing and sample data every 12h
CMD ["10", "230400"]

