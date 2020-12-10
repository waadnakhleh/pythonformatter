import ast


class Rewrite(ast.NodeVisitor):
    def __init__(self):
        self.indentation = 0

    def __enter__(self):
        self.indentation += 4

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.indentation -= 4

    def print(self, value, new_line_at_end = False):
        file.write(str(value))
        if new_line_at_end:
            file.write("\n")

    def visit_Tuple(self, node):
        file.write("(")
        for i, val in enumerate(node.elts):
            self.print(val.value)
            if len(node.elts) != i + 1:
                self.print(f", ")
        self.print(")", new_line_at_end=True)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            file.write(f'"{node.value}"\n')

        else:
            file.write(f"{node.value}\n")

    def visit_Import(self, node):
        imports_list = node.names
        for name in imports_list:
            file.write(f"import {name.name}\n")

    def visit_ImportFrom(self, node):
        import_list = node.names
        file.write(f"from {node.module} import ")
        for i, name in enumerate(import_list):
            file.write(f"{name.name}")
            if i + 1 != len(import_list):
                file.write(", ")
            else:
                file.write("\n")


def rewrite(file_name: str):
    with open(file_name) as f:
        try:
            parsed = ast.parse(f.read(), file_name)  # the AST of the .py file
            Rewrite().visit(parsed)
        except SyntaxError as e:
            raise e  # Raise error if ast module couldn't parse file.p
        file.close()


file = open("modified_file.py", "a")
