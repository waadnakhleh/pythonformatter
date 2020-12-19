import filecmp
import pytest
import _rewrite


def confirm(output):
    compare_to = "modified_file.py"
    assert filecmp.cmp(output, compare_to)
    open(compare_to, 'w').close()  # Empty file


def make_test(input_file, output_file):
    _rewrite.rewrite(input_file)
    confirm(output_file)
    _rewrite.file = open("modified_file.py", "a")


def test_syntax_error():
    with pytest.raises(SyntaxError):
        _rewrite.rewrite("syntax_error/file.py")


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


def test_boolop():
    input_file, output_file = "test_boolop/input.py", "test_boolop/output.py"
    make_test(input_file, output_file)


def test_list():
    input_file, output_file = "test_list/input.py", "test_list/output.py"
    make_test(input_file, output_file)


def test_tuple():
    input_file, output_file = "test_tuple/input.py", "test_tuple/output.py"
    make_test(input_file, output_file)


def test_pass():
    input_file, output_file = "test_pass/input.py", "test_pass/output.py"
    make_test(input_file, output_file)


def test_assignment():
    input_file, output_file = "test_assignment/input.py", "test_assignment/output.py"
    make_test(input_file, output_file)


def test_binop():
    input_file, output_file = "test_binop/input.py", "test_binop/output.py"
    make_test(input_file, output_file)


def test_namedexpr():
    input_file, output_file = "test_namedexpr/input.py", "test_namedexpr/output.py"
    make_test(input_file, output_file)


def test_compare():
    input_file, output_file = "test_compare/input.py", "test_compare/output.py"
    make_test(input_file, output_file)


def test_assert():
    input_file, output_file = "test_assert/input.py", "test_assert/output.py"
    make_test(input_file, output_file)


def test_if():
    input_file, output_file = "test_if/input.py", "test_if/output.py"
    make_test(input_file, output_file)


def test_while():
    input_file, output_file = "test_while/input.py", "test_while/output.py"
    make_test(input_file, output_file)


def test_break():
    input_file, output_file = "test_break/input.py", "test_break/output.py"
    make_test(input_file, output_file)


def test_continue():
    input_file, output_file = "test_continue/input.py", "test_continue/output.py"
    make_test(input_file, output_file)


def test_return():
    input_file, output_file = "test_return/input.py", "test_return/output.py"
    make_test(input_file, output_file)


def test_call():
    input_file, output_file = "test_call/input.py", "test_call/output.py"
    make_test(input_file, output_file)


def test_functiondef():
    input_file, output_file = "test_functiondef/input.py", "test_functiondef/output.py"
    make_test(input_file, output_file)


def test_for():
    input_file, output_file = "test_for/input.py", "test_for/output.py"
    make_test(input_file, output_file)


def test_augassign():
    input_file, output_file = "test_augassign/input.py", "test_augassign/output.py"
    make_test(input_file, output_file)