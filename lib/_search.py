import os


def walk(root_directory: str, files_list: list, suffixes: list):
    """
    Gathers all permitted files to be formatted and saves the files in a list
    :param root_directory: Root directory of the files to search in
    :param files_list: List to append to the file names
    :param suffixes: A list containing the allowed suffixes to reformat
    :return: None
    """
    for path, subdirs, files in os.walk(root_directory):
        for name in files:
            if (
                any(name.endswith(suffix) for suffix in suffixes)
            ) and "venv" not in path:
                files_list.append(os.path.join(path, name))
