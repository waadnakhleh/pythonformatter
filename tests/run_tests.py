import _rewrite
import filecmp


def confirm(output):
    compare_to = "modified_file.py"
    assert filecmp.cmp(output, compare_to)
    open(compare_to, 'w').close()  # Empty file


def make_test(input_file, output_file):
    _rewrite.rewrite(input_file)
    confirm(output_file)
    _rewrite.file = open("modified_file.py", "a")


def test_import():
    input_file, output_file = "test_import/input.py", "test_import/output.py"
    make_test(input_file, output_file)


def test_from_import():
    input_file, output_file = "test_from_import/input.py", "test_from_import/output.py"
    make_test(input_file, output_file)


def test_constant():
    # TODO: fix bug, binary and hex values change to decimal.
    input_file, output_file = "test_constant/input.py", "test_constant/output.py"
    make_test(input_file, output_file)


def test_unaryop():
    input_file, output_file = "test_unaryop/input.py", "test_unaryop/output.py"
    make_test(input_file, output_file)


def test_name():
    input_file, output_file = "test_name/input.py", "test_name/output.py"
    make_test(input_file, output_file)
