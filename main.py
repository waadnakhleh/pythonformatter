import ast


def main():
    # User must insert file name
    file_name = input()
    with open(file_name) as f:
        file = open("modified_file.py", "a")
        try:
            parsed = ast.parse(f.read(), file_name)  # the AST of the .pytsl file
        except SyntaxError as e:
            raise e


if __name__ == '__main__':
    main()
