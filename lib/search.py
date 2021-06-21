import os


def walk(root: str, files_list: list):
    for path, subdirs, files in os.walk(root):
        for name in files:
            if name[-2:] == "py" and "venv" not in path:
                files_list.append(os.path.join(path, name))
