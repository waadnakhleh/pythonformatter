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
        else:
            for char in conf_dict["DIRECT_FILE"]:
                print("1", char)
        visitor.direct_file = conf_dict["DIRECT_FILE"]

    @staticmethod
    def parse_arguments(argv, visitor):
        i = 0
        while i < len(argv):
            if argv[i] == "--target-file":
                visitor.target_file = argv[i+1]
            elif argv[i] == "--max-line":
                visitor.max_line = int(argv[i+1])
            i += 1
