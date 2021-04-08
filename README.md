# Python Formatter

Python Formatter is a Python library for reformatting Python code.
Python Formatter works with Python 3.8 and under the guidelines of PEP8, but can be customized to the developer needs.

## Installation and dependencies

1. Clone the repository:

    `git clone https://github.com/waadnakhleh/pythonformatter.git`
2. Install the dependencies:
    `pip install -r requirements.txt`

## Usage

```python
python -m main --target-file <filename>
```
To see other command line arguments use the --help argument
```python
python -m main --help
```

## Contributing
### To contribute:
1. Choose an issue from our issues list.
2. Make sure you have the latest version.
3. Make the changes.
4. Run black.
5. git add <changed_file>
6. git commit -m "good commit message"
7. git push origin <branch_name>

### Coding guidelines.
We follow the set of rules provided by PEP8. But since we run black on the code just make sure to:
1. Variable and function names should be in snake_case format.
2. Class names should be in CamelCase format.
3. Clear variable names (no ugly shortcuts).
4. Document your code clearly using docstrings.

### Useful links for contributors
1. [Python documentation for ast module](https://docs.python.org/3/library/ast.html)
2. [Unofficial expanded documentation](https://greentreesnakes.readthedocs.io/en/latest/)
3. [Useful article about Python ast module](https://medium.com/@kamneemaran45/python-ast-5789a1b60300)

## License
We don't really have a license. If we ever compete with other code formatters it will be MIT.
