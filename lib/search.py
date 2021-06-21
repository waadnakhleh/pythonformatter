import os


def walk(root_directory: str, files_list: list, suffixes: list):
    for path, subdirs, files in os.walk(root_directory):
        for name in files:
            if (
                any(name.endswith(suffix) for suffix in suffixes)
            ) and "venv" not in path:
                files_list.append(os.path.join(path, name))
