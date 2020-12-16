import ast


class Rewrite(ast.NodeVisitor):
    def __init__(self):
        self.indentation = 0

    def __enter__(self):
        self.indentation += 4

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.indentation -= 4

    def _prepare_line(self, value, _new_line, _is_iterable, _special_attribute):
        """
        Prepares a line to be printed.
        :param value: Value required to print.
        :param _new_line: End line with a \n.
        :param _is_iterable: Is the value iterable (list, tuple, etc...).
        :param _special_attribute: Special attribute that we need to print instead of value.
        :return: None.
        """
        to_print = " " * self.indentation  # Prepare indentation first.
        if _is_iterable:
            assert hasattr(value, "__iter__")  # Make sure the item is iterable.
            iterable_size = len(value)
            for i, item in enumerate(value):
                to_print += str(item) if not _special_attribute else f"{getattr(item, _special_attribute)}"
                if i + 1 != iterable_size:
                    to_print += ", "
        else:
            to_print += f"{value}" if not _special_attribute else f"{getattr(value, _special_attribute)}"
        if _new_line:
            to_print += "\n"
        return to_print

    def print(self, value, *, _new_line=False, _is_iterable=False, _special_attribute=None):
        """
        outputs required value to target file.
        :param value: Value required to print.
        :param _new_line: End line with a \n.
        :param _is_iterable: Is the value iterable (list, tuple, etc...).
        :param _special_attribute: Special attribute that we need to print instead of value.
        :return: None.
        """
        to_print = self._prepare_line(value, _new_line, _is_iterable, _special_attribute)
        file.write(to_print)

    def visit_Import(self, node):
        imports_list = node.names
        for name in imports_list:
            self.print(f"import {name.name}", _new_line=True)

    def visit_ImportFrom(self, node):
        import_list = node.names
        self.print(f"from {node.module} import ")
        self.print(import_list, _new_line=True, _is_iterable=True, _special_attribute="name")


def rewrite(file_name: str):
    with open(file_name) as f:
        try:
            parsed = ast.parse(f.read(), file_name)  # the AST of the .py file
            Rewrite().visit(parsed)
        except SyntaxError as e:
            raise e
        file.close()


file = open("modified_file.py", "a")
