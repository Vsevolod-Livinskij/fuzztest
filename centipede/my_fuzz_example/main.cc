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
    std::string inp_choice_seq_file =
        std::filesystem::path(temp_dir).append(absl::StrCat("input"));
    WriteToLocalFile(inp_choice_seq_file, input);

    Command cmd{
        "/testing/result/yarpgen",
        {"--check-algo=asserts",
         "--param-shuffle=false",
         "--choice-seq-load-file=" + inp_choice_seq_file,
         "-o " + temp_dir,
        },
    };

    bool success = cmd.Execute() == 0;
    if (!success) {
      LOG(ERROR) << "Failed to generate";
      LOG(ERROR) << "Input: " << input.data();
      std::string new_binary(binary);
      new_binary += " --version";
      return ExecuteCentipedeSancovBinaryWithShmem(new_binary, inputs,
                                                   batch_result) == 0;
    }

    LOG(INFO) << "Generation: " << success;

    std::string driver_cpp =
        std::filesystem::path(temp_dir).append(absl::StrCat("driver.cpp"));
    std::string driver_o =
        std::filesystem::path(temp_dir).append(absl::StrCat("driver.o"));
    Command driver_comp{
        "clang++",
        {driver_cpp, "-c -w -O3", "-o " + driver_o},
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
        {driver_o, func_o, "-O3", "-o " + exec_file},
    };
    success = exec_compile.Execute() == 0;
    if (!success) {
      LOG(INFO) << "Failed to compile exec";
      return false;
    }

    LOG(INFO) << "Compilation: " << success;

    Command exec_test{exec_file};
    success = exec_test.Execute() == 0;
    if (!success) {
      LOG(INFO) << "Failed to execute";
    }
    return success;
  }

  void Mutate(const std::vector<MutationInputRef>& inputs, size_t num_mutants,
                std::vector<ByteArray>& mutants) override {
    LOG(INFO) << "Mutation started";

    std::string Prefix = "// ";

    // Create a temporary directory
    const std::string temp_dir = TemporaryLocalDirPath();
    CHECK(!temp_dir.empty());
    LOG(INFO) << "Temp dir: " << temp_dir;

    // Read inputs to a choice sequence and mutate them
    auto input = inputs.front();
    std::string Str(input.data.begin(), input.data.end());
    std::stringstream SS(Str);
    tree_guide::FileGuide FG;
    FG.setSync(tree_guide::Sync::RESYNC);
    //FG.setSync(tree_guide::Sync::NONE);
    if (!FG.parseChoices(SS, Prefix)) {
      LOG(ERROR) << "ERROR: couldn't parse choices from: \n" << SS.str();
      mutants.emplace_back(input.data.begin(), input.data.end());
      return;
    }
    auto C = FG.getChoices();
    LOG(INFO) << "Parsed choices num: " << C.size();
    mutator::mutate_choices(C);
    LOG(INFO) << "Mutation complete";
    FG.replaceChoices(C);
    LOG(INFO) << "Mutated choices num: " << FG.getChoices().size();

    // Create a Saver guide to dump the mutated choice sequence
    LOG(INFO) << "Dumping mutated choice sequence";
    tree_guide::SaverGuide SG(&FG, Prefix);
    auto Ch = SG.makeChooser();
    auto SaverCh = static_cast<tree_guide::SaverChooser*>(Ch.get());
    SaverCh->overrideChoices(C);
    assert(SaverCh);

    // Normalize the choice sequence
    LOG(INFO) << "Normalizing choice sequence";
    std::string choice_seq_str = SaverCh->formatChoices();
    LOG(INFO) << "Choice sequence to normalize len: " << choice_seq_str.size();
    std::string temp_inp_file =
        std::filesystem::path(temp_dir).append(absl::StrCat("input"));
    std::string temp_out_file =
        std::filesystem::path(temp_dir).append(absl::StrCat("output"));
    WriteToLocalFile(temp_inp_file, choice_seq_str);
    Command cmd{"/testing/result/yarpgen",
                {"--single-file=true", "--param-shuffle=false",
                 "--choice-seq-load-file=" + temp_inp_file,
                 "--choice-seq-save-file=" + temp_out_file, "-o " + temp_dir}};

    LOG(INFO) << "Normalization cmd: " << cmd.ToString();
    bool success = cmd.Execute() == 0;
    if (!success) {
      LOG(ERROR) << "Failed to normalize";
      mutants.emplace_back(input.data.begin(), input.data.end());
      return;
    }

    // Read the normalized choice sequence
    LOG(INFO) << "Reading normalized choice sequence";
    tree_guide::FileGuide FG_new;
    FG_new.parseChoices(temp_out_file, Prefix);
    tree_guide::SaverGuide SG2(&FG_new, Prefix);
    auto Ch_new = SG2.makeChooser();
    auto SaverCh_new = static_cast<tree_guide::SaverChooser*>(Ch_new.get());
    SaverCh_new->overrideChoices(FG_new.getChoices());
    auto choice_seq_str_new = SaverCh_new->formatChoices();
    mutants.emplace_back(choice_seq_str_new.begin(), choice_seq_str_new.end());

    LOG(INFO) << "Mutant len: " << choice_seq_str_new.size();
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
// rm -rf /testing/result/centipede-run/* && ./main --binary="/testing/llvm/centipede_build_llvmorg-17.0.3/bin/clang++ -O3 -w" --workdir=/testing/result/centipede-run/ --num_runs=10 --batch_size=1 --rss_limit_mb=0 --address_space_limit_mb=0 --timeout_per_input=120 --timeout_per_batch=240 --corpus_dir=/testing/result/guided-corpus --max_len=100000

int main(int argc, char **argv) {
  const auto leftover_argv = centipede::config::InitCentipede(argc, argv);
  // Reads flags; must happen after ParseCommandLine().
  const auto env = centipede::CreateEnvironmentFromFlags(leftover_argv);
  centipede::DefaultCallbacksFactory<centipede::MyCentipedeCallbacks> callbacks_factory;
  mutator::init(env.seed);
  return centipede::CentipedeMain(env, callbacks_factory);
}
