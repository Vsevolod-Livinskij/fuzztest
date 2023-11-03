#include <string>
#include <fstream>
#include <iostream>

int fuzzMe(const std::string &data) {
  if (data.size() == 4 && data[0] == 'f' && data[1] == 'u' && data[2] == 'z' &&
      data[3] == 'Z') {
    abort();
  }
  return 0;
}

int main(int argc, char *argv[]) {
  if (argc < 2) {
    return 0;
  }
  std::cout << argv[1] << std::endl;
  std::ifstream inp_file(argv[1]);
  if (!inp_file) return 0;
  std::string data;
  bool ret = false;
  if (getline(inp_file, data)) {
    ret = fuzzMe(data);
  }
  inp_file.close();
  return ret;
}
