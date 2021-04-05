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
                conf_dict[key] = value

        visitor.max_line = int(conf_dict["MAX_LINE"])
