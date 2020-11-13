import ast


class Rewrite(ast.NodeVisitor):
    def visit_Import(self, node):
        imports_list = node.names
        for name in imports_list:
            file.write(f"import {name.name}\n")


def rewrite(file_name: str):
    with open(file_name) as f:
        try:
            parsed = ast.parse(f.read(), file_name)  # the AST of the .pytsl file
            Rewrite().visit(parsed)
        except SyntaxError as e:
            raise e
        file.close()


file = open("modified_file.py", "a")
