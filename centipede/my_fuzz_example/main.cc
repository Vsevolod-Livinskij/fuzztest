#include "./centipede/centipede_callbacks.h"
#include "./centipede/config_file.h"
#include "./centipede/environment_flags.h"
#include "./centipede/util.h"
#include "./centipede/my_fuzz_example/guide.h"
#include "./centipede/my_fuzz_example/mutate.h"
#include "./centipede/command.h"

namespace centipede {
namespace {

static bool DEBUG_PLUGIN = false;

extern "C" size_t CentipedeGetExecutionResult(uint8_t *data, size_t capacity);
extern "C" void CentipedeClearExecutionResult();

class MyCentipedeCallbacks : public CentipedeCallbacks {
 public:
  explicit MyCentipedeCallbacks(const Environment& env)
      : CentipedeCallbacks(env) {}

  bool Execute(std::string_view binary, const std::vector<ByteArray>& inputs,
               BatchResult& batch_result) override {
    const std::string temp_dir = TemporaryLocalDirPath();
    CHECK(!temp_dir.empty());

    LOG(INFO) << "Temp dir: " << temp_dir;

    auto input = inputs.front();
    auto input_str = std::string(input.begin(), input.end());
    LOG(INFO) << "Input: " << input_str;

    Command cmd{
        "/testing/result/yarpgen",
        {"--check-algo=asserts", "-o " + temp_dir, "--seed=" + input_str},
    };

    bool success = cmd.Execute() == 0;
    if (!success) {
      LOG(INFO) << "Failed to generate";
      return false;
    }

    LOG(INFO) << "Generation: " << success;

    std::string driver_cpp =
        std::filesystem::path(temp_dir).append(absl::StrCat("driver.cpp"));
    std::string driver_o =
        std::filesystem::path(temp_dir).append(absl::StrCat("driver.o"));
    Command driver_comp{
        "clang++",
        {driver_cpp, "-c -w", "-o " + driver_o},
    };
    success = driver_comp.Execute() == 0;
    if (!success) {
      LOG(INFO) << "Failed to compile driver";
      return false;
    }

    std::string func_cpp =
        std::filesystem::path(temp_dir).append(absl::StrCat("func.cpp"));
    std::string func_o =
        std::filesystem::path(temp_dir).append(absl::StrCat("func.o"));
    std::string new_binary(binary);
    new_binary += " " + func_cpp + " -c " + "-o " + func_o;
    LOG(INFO) << "New binary: " << new_binary;
    success = ExecuteCentipedeSancovBinaryWithShmem(new_binary, inputs,
                                                    batch_result) == 0;
    if (!success) {
      LOG(INFO) << "Failed to compile func";
      return false;
    }

    std::string exec_file =
        std::filesystem::path(temp_dir).append(absl::StrCat("a.out"));
    Command exec_compile{
        "clang++",
        {driver_o, func_o, "-o " + exec_file},
    };
    success = exec_compile.Execute() == 0;
    if (!success) {
      LOG(INFO) << "Failed to compile exec";
      return false;
    }

    LOG(INFO) << "Compilation: " << success;

    Command cmd2{exec_file};
    success = cmd2.Execute() == 0;
    if (!success) {
      LOG(INFO) << "Failed to execute";
    }
    return success;
  }

  void Mutate(const std::vector<MutationInputRef>& inputs, size_t num_mutants,
                std::vector<ByteArray>& mutants) override {
    LOG(INFO) << "Mutate";
    auto input = inputs.front();
    auto input_str = std::string(input.data.begin(), input.data.end());
    LOG(INFO) << "Input: " << input_str;

    uint64_t seed = 0;
    for (auto c : input_str) {
      seed ^= c + 0x9e3779b9 + (seed<<6) + (seed>>2);
    }

    LOG(INFO) << "Seed: " << seed;
    auto mutant_str = std::to_string(seed);
    ByteArray mutant(mutant_str.begin(), mutant_str.end());
    mutants.push_back(mutant);

    /*
    const std::string temp_dir = TemporaryLocalDirPath();
    CHECK(!temp_dir.empty());

    LOG(INFO) << "Temp dir: " << temp_dir;

    auto input = inputs.front();

    std::string Prefix = "// ";
    std::string Generator = "yarpgen";

    std::string Str(input.data.begin(), input.data.end());
    std::stringstream SS(Str);
    tree_guide::FileGuide FG;
    // FG.setSync(tree_guide::Sync::RESYNC);
    FG.setSync(tree_guide::Sync::NONE);
    if (!FG.parseChoices(SS, Prefix)) {
      std::cerr << "ERROR: couldn't parse choices from:\n";
      std::cerr << SS.str();
      std::cerr << "--------------------------\n\n";
      exit(-1);
    }
    auto C = FG.getChoices();
    if (DEBUG_PLUGIN) std::cerr << "parsed " << C.size() << " choices\n";
    mutator::mutate_choices(C);
    if (DEBUG_PLUGIN) std::cerr << "mutated\n";
    FG.replaceChoices(C);

    tree_guide::SaverGuide SG(&FG, Prefix);
    auto Ch = SG.makeChooser();
    auto Ch2 = static_cast<tree_guide::SaverChooser*>(Ch.get());
    assert(Ch2);

    std::string choice_seq_str = Ch2->formatChoices();
    LOG(INFO) << "Orig: " << choice_seq_str;
    std::string temp_inp_file_path =
        std::filesystem::path(temp_dir).append(absl::StrCat("input"));
    std::string temp_out_file_path =
        std::filesystem::path(temp_dir).append(absl::StrCat("output"));
    WriteToLocalFile(temp_inp_file_path, choice_seq_str);
    Command cmd{
        Generator,
        {"--merge-vars-decl=true", "--do-not-emit=true"},
        {std::string("FILEGUIDE_INPUT_FILE=") + temp_inp_file_path,
         std::string("FILEGUIDE_OUTPUT_FILE=") + temp_out_file_path}
    };

    bool success = cmd.Execute() == 0;

    LOG(INFO) << "Normalization: " << success;

    tree_guide::FileGuide FG2;
    FG2.parseChoices(temp_out_file_path, Prefix);
    tree_guide::SaverGuide SG2(&FG2, Prefix);
    auto Ch3 = SG.makeChooser();
    auto Ch4 = static_cast<tree_guide::SaverChooser*>(Ch3.get());
    auto choice_seq_str2 = Ch4->formatChoices();
    mutants.push_back(ByteArray(choice_seq_str2.begin(),
    choice_seq_str2.end()));

    LOG(INFO) << "Mutant: " << choice_seq_str2;
     */
  }
    /*
    // Prepare input


    // Prepare the feature collection
    std::string output;
    const size_t output_size = 2048;
    output.resize(output_size);

    CentipedeClearExecutionResult();

    // Run
    Command cmd {
        env_.binary, {temp_file_path},
    };
    const int retval = cmd.Execute();

    // Get features
    const size_t offset = CentipedeGetExecutionResult(
        reinterpret_cast<uint8_t*>(output.data()), output.size());
    if (offset == 0) {
      std::cerr << "Failed to dump output execution results.";
      return EXIT_FAILURE;
    }

    batch_result.results().resize(inputs.size());
    BlobSequence blob_seq(reinterpret_cast<uint8_t*>(output.data()), output.size());
    batch_result.Read(blob_seq);

    return retval == 0;
    */
};

/*
class MyCentipedeCallbacks : public CentipedeDefaultCallbacks {
 public:
  explicit MyCentipedeCallbacks(const Environment& env)
      : CentipedeDefaultCallbacks(env) {}
};
*/
}
//   int main(int argc, char **argv) {
//     InitGoogle(argv[0], &argc, &argv, /*remove_flags=*/true);
//     centipede::Environment env;  // reads FLAGS.
//     centipede::DefaultCallbacksFactory<MyCentipedeCallbacks>
//     callbacks_factory; return centipede::CentipedeMain(env,
//     callbacks_factory);
//   }
int CentipedeMain(const Environment& env,
                  CentipedeCallbacksFactory& callbacks_factory);

}  // namespace centipede

// Run command
//rm -rf /testing/result/centipede-run/* && ./main --binary="/testing/llvm/centipede_build_llvmorg-17.0.3/bin/clang++ -O3 -w" --workdir=/testing/result/centipede-run/ --num_runs=1000 --batch_size=1 --rss_limit_mb=0 --address_space_limit_mb=0 --timeout_per_input=120 --timeout_per_batch=240 --corpus_dir=/testing/result/int-corpus

int main(int argc, char **argv) {
  const auto leftover_argv = centipede::config::InitCentipede(argc, argv);
  // Reads flags; must happen after ParseCommandLine().
  const auto env = centipede::CreateEnvironmentFromFlags(leftover_argv);
  centipede::DefaultCallbacksFactory<centipede::MyCentipedeCallbacks> callbacks_factory;
  return centipede::CentipedeMain(env, callbacks_factory);
}
