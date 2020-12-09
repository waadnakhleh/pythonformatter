import ast


class Rewrite(ast.NodeVisitor):
    def __init__(self):
        self.indentation = 0

    def __enter__(self):
        self.indentation += 4

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.indentation -= 4

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
            parsed = ast.parse(f.read(), file_name)  # the AST of the .pytsl file
            Rewrite().visit(parsed)
        except SyntaxError as e:
            raise e
        file.close()


file = open("modified_file.py", "a")
