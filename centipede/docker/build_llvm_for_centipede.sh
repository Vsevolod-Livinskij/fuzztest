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
git clone "$LLVM_REPO" "llvm_src" 2> /dev/null || (cd "llvm_src" ; git fetch "$LLVM_REPO" && git checkout origin/$LLVM_VERSION)
mkdir centipede_build_$LLVM_VERSION centipede_bin_$LLVM_VERSION
cd $LLVM_HOME/llvm_src
git checkout $LLVM_VERSION
echo $LLVM_REPO:$LLVM_VERSION > $LLVM_HOME/llvm_rev.txt
git log --format="%H" -n 1 >> $LLVM_HOME/llvm_rev.txt

# Pre-compilation steps
cd $LLVM_HOME/centipede_build_$LLVM_VERSION
CC=clang \
CXX=clang++ \
CXXFLAGS="-DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION -fno-builtin -fsanitize-coverage=trace-pc-guard,pc-table,trace-cmp -gline-tables-only -fsanitize-coverage-allowlist=/allowlist.txt" \
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

# A hack that allows us to use libcentipede_runner_no_main.a. Without it, we can't get the coverage instrumentation that we need
# TODO: is there a better way to do it?
cd $LLVM_HOME/centipede_build_$LLVM_VERSION
clang++ -DFUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION -fno-builtin -fsanitize-coverage=trace-pc-guard,pc-table,trace-cmp -gline-tables-only -fsanitize-coverage-allowlist=/allowlist.txt -fPIC -fno-semantic-interposition -fvisibility-inlines-hidden -Werror=date-time -Werror=unguarded-availability-new -Wall -Wextra -Wno-unused-parameter -Wwrite-strings -Wcast-qual -Wmissing-field-initializers -pedantic -Wno-long-long -Wc++98-compat-extra-semi -Wimplicit-fallthrough -Wcovered-switch-default -Wno-noexcept-type -Wnon-virtual-dtor -Wdelete-non-virtual-dtor -Wsuggest-override -Wstring-conversion -Wmisleading-indentation -Wctad-maybe-unsupported -fdiagnostics-color -ffunction-sections -fdata-sections -fno-common -Woverloaded-virtual -Wno-nested-anon-types -O3 -DNDEBUG -Wl,--export-dynamic  -Wl,-rpath-link,$LLVM_HOME/centipede_build_$LLVM_VERSION/./lib tools/clang/tools/driver/CMakeFiles/clang.dir/driver.cpp.o tools/clang/tools/driver/CMakeFiles/clang.dir/cc1_main.cpp.o tools/clang/tools/driver/CMakeFiles/clang.dir/cc1as_main.cpp.o tools/clang/tools/driver/CMakeFiles/clang.dir/cc1gen_reproducer_main.cpp.o tools/clang/tools/driver/CMakeFiles/clang.dir/clang-driver.cpp.o -o bin/clang-18  -Wl,-rpath,"\$ORIGIN/../lib:"  lib/libLLVMX86CodeGen.a  lib/libLLVMX86AsmParser.a  lib/libLLVMX86Desc.a  lib/libLLVMX86Disassembler.a  lib/libLLVMX86Info.a  lib/libLLVMAnalysis.a  lib/libLLVMCodeGen.a  lib/libLLVMCore.a  lib/libLLVMipo.a  lib/libLLVMAggressiveInstCombine.a  lib/libLLVMInstCombine.a  lib/libLLVMInstrumentation.a  lib/libLLVMMC.a  lib/libLLVMMCParser.a  lib/libLLVMObjCARCOpts.a  lib/libLLVMOption.a  lib/libLLVMScalarOpts.a  lib/libLLVMSupport.a  lib/libLLVMTargetParser.a  lib/libLLVMTransformUtils.a  lib/libLLVMVectorize.a  lib/libclangBasic.a  lib/libclangCodeGen.a  lib/libclangDriver.a  lib/libclangFrontend.a  lib/libclangFrontendTool.a  lib/libclangSerialization.a  lib/libLLVMAsmPrinter.a  lib/libLLVMCFGuard.a  lib/libLLVMGlobalISel.a  lib/libLLVMSelectionDAG.a  lib/libLLVMMCDisassembler.a  lib/libclangCodeGen.a  lib/libLLVMCoverage.a  lib/libLLVMFrontendDriver.a  lib/libLLVMLTO.a  lib/libLLVMExtensions.a  lib/libLLVMPasses.a  lib/libLLVMCodeGen.a  lib/libLLVMCodeGenTypes.a  lib/libLLVMObjCARCOpts.a  lib/libLLVMTarget.a  lib/libLLVMCoroutines.a  lib/libLLVMipo.a  lib/libLLVMInstrumentation.a  lib/libLLVMVectorize.a  lib/libLLVMBitWriter.a  lib/libLLVMLinker.a  lib/libLLVMHipStdPar.a  lib/libLLVMIRPrinter.a  lib/libclangExtractAPI.a  lib/libclangRewriteFrontend.a  lib/libclangARCMigrate.a  lib/libclangStaticAnalyzerFrontend.a  lib/libclangStaticAnalyzerCheckers.a  lib/libclangStaticAnalyzerCore.a  lib/libclangCrossTU.a  lib/libclangIndex.a  lib/libclangFrontend.a  lib/libclangDriver.a  lib/libLLVMWindowsDriver.a  lib/libLLVMOption.a  lib/libclangParse.a  lib/libclangSerialization.a  lib/libclangSema.a  lib/libclangAnalysis.a  lib/libclangASTMatchers.a  lib/libLLVMFrontendHLSL.a  lib/libclangAPINotes.a  lib/libclangEdit.a  lib/libclangSupport.a  lib/libclangAST.a  lib/libclangFormat.a  lib/libclangToolingInclusions.a  lib/libclangToolingCore.a  lib/libclangRewrite.a  lib/libclangLex.a  lib/libclangBasic.a  lib/libLLVMFrontendOpenMP.a  lib/libLLVMScalarOpts.a  lib/libLLVMAggressiveInstCombine.a  lib/libLLVMInstCombine.a  lib/libLLVMFrontendOffloading.a  lib/libLLVMTransformUtils.a  lib/libLLVMAnalysis.a  lib/libLLVMProfileData.a  lib/libLLVMSymbolize.a  lib/libLLVMDebugInfoDWARF.a  lib/libLLVMDebugInfoPDB.a  lib/libLLVMDebugInfoMSF.a  lib/libLLVMDebugInfoBTF.a  lib/libLLVMObject.a  lib/libLLVMMCParser.a  lib/libLLVMMC.a  lib/libLLVMDebugInfoCodeView.a  lib/libLLVMIRReader.a  lib/libLLVMBitReader.a  lib/libLLVMAsmParser.a  lib/libLLVMTextAPI.a  lib/libLLVMCore.a  lib/libLLVMBinaryFormat.a  lib/libLLVMRemarks.a  lib/libLLVMBitstreamReader.a  lib/libLLVMTargetParser.a  lib/libLLVMSupport.a  lib/libLLVMDemangle.a  -lrt  -ldl  -lm  /usr/lib/x86_64-linux-gnu/libz.so  /usr/lib/x86_64-linux-gnu/libtinfo.so $FUZZTEST_HOME/bazel-bin/centipede/libcentipede_runner_no_main.a &&\
/usr/bin/cmake -E cmake_symlink_executable bin/clang-18 bin/clang && cd $LLVM_HOME/centipede_build_$LLVM_VERSION/tools/clang/tools/driver && /usr/bin/cmake -E create_symlink clang-18 $LLVM_HOME/centipede_build_$LLVM_VERSION/./bin/clang++ && cd $LLVM_HOME/centipede_build_$LLVM_VERSION/tools/clang/tools/driver && /usr/bin/cmake -E create_symlink clang-18 $LLVM_HOME/centipede_build_$LLVM_VERSION/./bin/clang-cl && cd $LLVM_HOME/centipede_build_$LLVM_VERSION/tools/clang/tools/driver && /usr/bin/cmake -E create_symlink clang-18 $LLVM_HOME/centipede_build_$LLVM_VERSION/./bin/clang-cpp


# Cleanup
#rm -rf $LLVM_HOME/centipede_build_$LLVM_VERSION $LLVM_HOME/llvm_src

