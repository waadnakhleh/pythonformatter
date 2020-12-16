import ast
import _ast
from _ast import AST


def iter_fields(node):
    """
    Yield a tuple of ``(fieldname, value)`` for each field in ``node._fields``
    that is present on *node*.
    """
    for field in node._fields:
        try:
            yield field, getattr(node, field)
        except AttributeError:
            pass


class Rewrite(ast.NodeVisitor):
    def __init__(self):
        self.indentation = 0

    def __enter__(self):
        self.indentation += 4

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.indentation -= 4

    def visit(self, node, new_line=True):
        """
        Visit a node, this overrides NodeVisitor visit method as we need to
        start a new line between each body element.
        """
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        visitor_ = visitor(node)
        if new_line and not isinstance(node, ast.Module):
            self.new_line()
        return visitor_

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        for field, value in iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, AST):
                        if isinstance(node, _ast.Module):
                            self.visit(item)
                        else:
                            self.visit(item, False)
            elif isinstance(value, AST):
                self.visit(value, False)

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

    def new_line(self):
        self.print("", _new_line=True)

    def visit_Import(self, node):
        imports_list = node.names
        for i, name in enumerate(imports_list):
            self.print(f"import {name.name}", _new_line=True if i + 1 != len(imports_list) else False)

    def visit_ImportFrom(self, node):
        import_list = node.names
        self.print(f"from {node.module} import ")
        self.print(import_list, _is_iterable=True, _special_attribute="name")

    def visit_UnaryOp(self, node):
        ops = {_ast.Not: "not", ast.Invert: "~", ast.UAdd: "+", ast.USub: "-"}
        self.print(f"{ops[type(node.op)]}")
        if isinstance(node.op, _ast.Not):
            self.print(" ")
        self.visit(node.operand, False)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            self.print('"')
        self.print(node.value)
        if isinstance(node.value, str):
            self.print('"')

    def visit_Name(self, node):
        self.print(node.id)


def rewrite(file_name: str):
    global file
    file = open("modified_file.py", "a")
    with open(file_name) as f:
        try:
            parsed = ast.parse(f.read(), file_name)  # the AST of the .py file
            Rewrite().visit(parsed)
        except SyntaxError as e:
            raise e
        file.close()


file = None
