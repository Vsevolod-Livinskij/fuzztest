#include "./centipede/centipede_callbacks.h"
//#include "./centipede/environment.h"
#include "./centipede/config_file.h"
#include "./centipede/environment_flags.h"
//#include "./centipede/runner_interface.h"

/*
#include "./centipede/centipede_default_callbacks.h"
#include "./centipede/config_file.h"
#include "./centipede/environment_flags.h"
*/

namespace centipede {
namespace {

extern "C" size_t CentipedeGetExecutionResult(uint8_t *data, size_t capacity);
extern "C" void CentipedeClearExecutionResult();

class MyCentipedeCallbacks : public CentipedeCallbacks {
 public:
  explicit MyCentipedeCallbacks(const Environment& env)
      : CentipedeCallbacks(env) {}

  bool Execute(std::string_view binary, const std::vector<ByteArray>& inputs,
               BatchResult& batch_result) override {
    return ExecuteCentipedeSancovBinaryWithShmem(binary, inputs, batch_result) ==
           0;
    /*
    // Prepare input
    const std::string temp_dir = TemporaryLocalDirPath();
    CHECK(!temp_dir.empty());
    CreateLocalDirRemovedAtExit(temp_dir);

    const std::string temp_file_path =
        std::filesystem::path(temp_dir).append(absl::StrCat("input"));
    WriteToLocalFile(temp_file_path, inputs.front());

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
  }
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

int main(int argc, char **argv) {
  const auto leftover_argv = centipede::config::InitCentipede(argc, argv);
  // Reads flags; must happen after ParseCommandLine().
  const auto env = centipede::CreateEnvironmentFromFlags(leftover_argv);
  centipede::DefaultCallbacksFactory<centipede::MyCentipedeCallbacks> callbacks_factory;
  return centipede::CentipedeMain(env, callbacks_factory);
}
