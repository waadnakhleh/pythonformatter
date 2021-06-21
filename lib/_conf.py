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
                if line[0] == "#":
                    # If the leading char in the line is "#", treat it as a comment.
                    continue
                key, value = line.split("=")
                conf_dict[key] = value.split("\n")[0]

        visitor.max_line = int(conf_dict["MAX_LINE"])
        visitor.vertical_definition_lines = int(conf_dict["VERTICAL_DEFINITION_LINES"])
        visitor.nested_lines = int(conf_dict["NESTED_LINES"])
        if str(conf_dict["DIRECT_FILE"]) == "TRUE":
            visitor.direct_file = True
            visitor.target_file = os.path.join(parent_dir, "file.py")
        if str(conf_dict["CHECK_ONLY"]) == "TRUE":
            visitor.check_only = True
        if str(conf_dict["SPACE_BETWEEN_ARGUMENTS"]) == "TRUE":
            visitor.space_between_arguments = True
        if str(conf_dict["MULTIPLE_IMPORTS"]) == "TRUE":
            visitor.multiple_imports = True
        if str(conf_dict["DIRECTORY"]) == "TRUE":
            assert (
                not visitor.direct_file
            ), "cannot use directory with direct_file = True"

        # Get all suffixes and remove leading and ending whitespaces.
        suffixes = conf_dict["SUFFIXES"].split(",")
        for suffix in suffixes:
            visitor.allowed_suffixes.append(suffix.strip())

        visitor.direct_file = conf_dict["DIRECT_FILE"]

    @staticmethod
    def parse_arguments(argv, visitor):
        i = 0
        while i < len(argv):
            if argv[i] in ["-d", "--directory"]:
                visitor.direct_file = False
                visitor.directory = argv[i + 1]
                i += 1
            elif argv[i] in ["-t", "--target-file"]:
                visitor.target_file = argv[i + 1]
                i += 1
            elif argv[i] in ["-ml", "--max-line"]:
                visitor.max_line = int(argv[i + 1])
                i += 1
            elif argv[i] in ["-nl", "--nested-lines"]:
                visitor.nested_lines = int(argv[i + 1])
                i += 1
            elif argv[i] in ["-vdl", "--vertical-definition-lines"]:
                visitor.vertical_definition_lines = int(argv[i + 1])
                i += 1
            elif argv[i] in ["-c", "--check-only"]:
                visitor.check_only = True
            elif argv[i] in ["--space-between-arguments"]:
                visitor.space_between_arguments = True
            elif argv[i] in ["-mi", "--multiple-imports"]:
                visitor.multiple_imports = True
            elif argv[i] in ["-h", "--help"]:
                print_help()
                exit(0)
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
            "-d",
            "--directory <directory_path>",
        ): "Reformat all python files in directory",
        (
            "-t",
            "--target-file <target_file>",
        ): "Specify the target file to be formatted",
    }

    options = {
        ("-c", "--check-only"): "Use this option to check if your code is formatted",
        ("-h", "--help"): "Display the help message",
        ("-ml", "--max-line <max_line>"): "Specify the maximum line length",
        (
            "-mi",
            "--multiple-imports",
        ): "Allow importing multiples modules in a single line",
        (
            "-nl",
            "--nested-lines <lines>",
        ): "Specify number of empty lines between nested definitions",
        (
            "",
            "--space-between-arguments",
        ): "Use spaces between arguments with default values",
        (
            "-vdl",
            "--vertical-definition-lines <number>",
        ): "Number of empty lines between definitions",
    }
    print("Usage: [SRC] [OPTIONS]\n")
    print("SRC:")
    print_section(src)
    print("OPTIONS:")
    print_section(options)


def print_section(messages):
    for key, value in messages.items():
        short, long = key
        message = f"  {short}, {long}" if short else f"  {long}"
        assert len(messages) < 55, "argument too long"
        spaces = 55 - len(message)
        message += " " * spaces
        message += value
        print(message)
