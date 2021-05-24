import os
import pathlib

current_dir = os.path.abspath(os.path.dirname(__file__))
parent_dir = pathlib.Path(current_dir).parent


class Conf:
    @staticmethod
    def set_configurations(conf_dict, visitor):
        with open(os.path.join(parent_dir, "conf.txt")) as f:
            lines = f.readlines()
            for line in lines:
                key, value = line.split("=")
                conf_dict[key] = value.split("\n")[0]

        visitor.max_line = int(conf_dict["MAX_LINE"])
        if str(conf_dict["DIRECT_FILE"]) == "TRUE":
            visitor.direct_file = True
            visitor.target_file = os.path.join(parent_dir, "file.py")
        elif str(conf_dict["CHECK_ONLY"]) == "TRUE":
            visitor.check_only = True
        else:
            pass
        visitor.direct_file = conf_dict["DIRECT_FILE"]

    @staticmethod
    def parse_arguments(argv, visitor):
        i = 0
        while i < len(argv):
            if argv[i] in ["--target-file", "-t"]:
                visitor.target_file = argv[i + 1]
                i += 1
            elif argv[i] in ["--max-line", "-ml"]:
                visitor.max_line = int(argv[i + 1])
                i += 1
            elif argv[i] in ["--help", "-h"]:
                print_help()
                exit(0)
            elif argv[i] in ["--check-only", "-c"]:
                visitor.check_only = True
            else:
                if i != 0:
                    raise ValueError(f"unknown argument {argv[i]}.")
            i += 1


def print_help():
    """
    Displays help message
    :return: None
    """
    src = {
        (
            "-t",
            "--target-file <target_file>",
        ): "Specify the target file to be formatted",
    }

    options = {
        ("-ml", "--max-line <max_line>"): "Specify the maximum line length",
        ("-h", "--help"): "Display the help message",
        ("-c", "--check-only"): "Use this option to check if your code is formatted",
    }
    print("Usage: [SRC] [OPTIONS]\n")
    print("SRC:")
    print_section(src)
    print("OPTIONS:")
    print_section(options)


def print_section(messages):
    for key, value in messages.items():
        short, long = key
        message = f"  {short}, {long}"
        assert len(messages) < 55, "argument too long"
        spaces = 55 - len(message)
        message += " " * spaces
        message += value
        print(message)
