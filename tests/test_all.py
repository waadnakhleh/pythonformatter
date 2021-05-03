import filecmp
import os
import pathlib
import pytest
from lib import _rewrite
import main


def confirm(output):
    compare_to = "modified_file.py"
    try:
        assert filecmp.cmp(output, compare_to)
    except AssertionError as e:
        with open(compare_to) as f:
            if not os.path.isdir("logs"):
                os.mkdir("logs")
            lines = f.readlines()
            lines = [l for l in lines]
            with open(
                f"logs/log_{output[:len(output)-len('/output.py')]}.py", "w"
            ) as f1:
                f1.writelines(lines)
        raise e
    finally:
        open(compare_to, "w").close()  # Empty file


def make_test(input_file, output_file, max_line=88):
    input_file = pathlib.Path(__file__).parent.absolute().joinpath(input_file)
    output_file = pathlib.Path(__file__).parent.absolute().joinpath(output_file)
    main.main("--target-file", input_file, "--max-line", max_line)
    confirm(output_file)
    _rewrite.file = open("modified_file.py", "a")


def test_syntax_error():
    with pytest.raises(SyntaxError):
        input_file = "syntax_error/file.py"
        input_file = pathlib.Path(__file__).parent.absolute().joinpath(input_file)
        main.main("--target-file", input_file)


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


def test_classdef():
    input_file, output_file = "test_classdef/input.py", "test_classdef/output.py"
    make_test(input_file, output_file)


def test_with():
    input_file, output_file = "test_with/input.py", "test_with/output.py"
    make_test(input_file, output_file)


def test_delete():
    input_file, output_file = "test_delete/input.py", "test_delete/output.py"
    make_test(input_file, output_file)


def test_attribute():
    input_file, output_file = "test_attribute/input.py", "test_attribute/output.py"
    make_test(input_file, output_file)


def test_try():
    input_file, output_file = "test_try/input.py", "test_try/output.py"
    make_test(input_file, output_file)


def test_raise():
    input_file, output_file = "test_raise/input.py", "test_raise/output.py"
    make_test(input_file, output_file)


def test_global():
    input_file, output_file = "test_global/input.py", "test_global/output.py"
    make_test(input_file, output_file)


def test_nonlocal():
    input_file, output_file = "test_nonlocal/input.py", "test_nonlocal/output.py"
    make_test(input_file, output_file)


def test_subscript():
    input_file, output_file = "test_subscript/input.py", "test_subscript/output.py"
    make_test(input_file, output_file)


def test_listcomp():
    input_file, output_file = "test_listcomp/input.py", "test_listcomp/output.py"
    make_test(input_file, output_file)


def test_docstring():
    input_file, output_file = "test_docstring/input.py", "test_docstring/output.py"
    make_test(input_file, output_file)


def test_ifexpr():
    input_file, output_file = "test_ifexpr/input.py", "test_ifexpr/output.py"
    make_test(input_file, output_file)


def test_dict():
    input_file, output_file = "test_dict/input.py", "test_dict/output.py"
    make_test(input_file, output_file)


def test_general():
    input_file, output_file = "test_general/input.py", "test_general/output.py"
    make_test(input_file, output_file)


def test_command_line_args():
    input_file, output_file = (
        "test_command_line_args/input.py",
        "test_command_line_args/output.py",
    )
    make_test(input_file, output_file, max_line=100)


def test_bad_arguments():
    with pytest.raises(ValueError, match="unknown argument --unsupported-argument"):
        main.main("--target-file", "input_file", "--unsupported-argument", "")
