import ast


class Rewrite(ast.NodeVisitor):
    pass


def rewrite(file_name: str):
    with open(file_name) as f:
        file = open("modified_file.py", "a")
        try:
            parsed = ast.parse(f.read(), file_name)  # the AST of the .pytsl file
            parsed.visit()
        except SyntaxError as e:
            raise e
