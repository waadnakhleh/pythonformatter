import ast
import _ast
import logging
import filecmp
import os
import _search
from lib import _conf
from collections import OrderedDict
from shutil import copyfile
from _exceptions import NoSolutionError

# Remove the following comment to see print log on stdout.
# To see more detailed logging, change level to logging.DEBUG.
# logging.getLogger().setLevel(logging.INFO)


class Rewrite(ast.NodeVisitor):
    def __init__(self):
        # Allowed file suffixes when using search by directory, the default suffix
        # contains .py suffix only and can be added through the conf.txt file.
        self.allowed_suffixes = []
        # The equivalent of each ast node and its symbol.
        self.ar_ops = {
            _ast.Add: "+",
            _ast.Sub: "-",
            _ast.Mult: "*",
            _ast.MatMult: "@",
            _ast.Div: "/",
            _ast.Mod: "%",
            _ast.Pow: "**",
            _ast.LShift: "<<",
            _ast.RShift: ">>",
            _ast.BitOr: "|",
            _ast.BitXor: "^",
            _ast.BitAnd: "&",
            _ast.FloorDiv: "//",
        }
        # Path of the configuration file, the default value is conf.txt but can be
        # by using -cfg or --configuration option.
        self.configuration_file = "conf.txt"
        # If check_only is set to True, the software only checks whether the code is
        # properly formatter or not.
        self.check_only = False
        # Line length.
        self.current_line_len = 0
        # Content of the current line.
        self.current_line = ""
        # If set to True, only one target will be reformatted, otherwise, the system
        # will look for all Python files in directory to reformat.  TODO finish.
        self.direct_file = True
        # The full path of a directory which includes python files to be reformatted,
        # if provided, the system will search recursively for all the python files
        # in the directory and its sub-directories.
        self.directory = None
        # Is this the first node that is part of a long node.
        self.first_long_node = False  # TODO name is not clear, choose better wording.
        # List containing all the python files that needs to be reformatted.
        # Note that this list will be used only when using --directory argument.
        self.files = []
        # Space indentation in any given moment.
        self.indentation = 0
        # True if the system is starting a new line, False otherwise.
        self.in_new_line = True
        # List which holds data about the nested body of a function, each item in the
        # list contains a tuple, the first value stores the node of the function, and
        # the second value holds a boolean value which indicates whether the nested
        # function is the last item in the body.
        # Note that in case of a function which does not include any nested function
        # declaration, the list will hold a tuple containing None values (None, None).
        self.last_body_node = []
        # True if the system is handling the last node in Module, False otherwise.
        self.last_node = False
        # True if the the system is handling the last node in a class body, False
        # otherwise.
        self.latest_class = False
        # Are we managing a node that exceeds the limit.
        self.long_node = False
        # Max line length, default value is 88 according to PEP8.
        self.max_line = 88
        # Allow importing multiples modules in a single line
        self.multiple_imports = False
        # Number of empty lines between nested function/class definitions
        self.nested_lines = 1
        # Scope level that indicates the indentation/nested levels.
        # The starting value is zero which translates to global scope, with each new
        # scope, the value will be incremented later decremented when the scope ends.
        self.nested_scope = 0
        # Print spaces between arguments with default values/keywords and their values
        # if set to True, otherwise, the equal sign will be right next the keyword and
        # the value.
        self.space_between_arguments = False
        # Latest node that starts a line (in body/function/class).
        self.starting_new_line_node = None
        # The path of the file to be formatter.
        # Note that target_file will be empty if and only if direct_file is also set to
        # True.
        self.target_file = ""
        # Number of empty lines between class/function definitions
        self.vertical_definition_lines = 2

    def __enter__(self):
        """
        Called when starting a nested scope, e.g. Functions body.
        Note that this function is called automatically when using "with" statement.
        """
        logging.info(f"Start indentation = {self.indentation + 4}")
        self.change_indentation(4)
        self.nested_scope += 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Called to close a scope, e.g. the end of a functions body.
        Note that this function is called automatically when using "with" statement.
        """
        logging.info(f"Close indentation = {self.indentation - 4}")
        self.change_indentation(-4)
        self.nested_scope -= 1

    def visit(self, node, new_line=True):
        """
        Visit a node, this overrides NodeVisitor visit method as we need to
        start a new line between each body element.
        """
        method = "visit_" + node.__class__.__name__
        # Get the visit_Class method, if not found, return generic_visit() method.
        visitor = getattr(self, method, self.generic_visit)
        logging.info(f"in visit(), visitor={visitor.__name__}")
        # Call the visitor function
        visitor_ = visitor(node)
        if new_line and not isinstance(node, ast.Module):
            self.new_line()
        return visitor_

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        logging.info(f"in generic_visit(), node={type(node).__name__}")
        for field, value in ast.iter_fields(node):
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
        to_print = ""
        if _new_line and not value:
            # Finish current line or start a new one.
            to_print = "\n"
            self.in_new_line = True
            return to_print
        if self.in_new_line:
            to_print = " " * self.indentation
            self.in_new_line = False
        if _is_iterable:
            assert hasattr(value, "__iter__")  # Make sure the item is iterable.
            iterable_size = len(value)
            for i, item in enumerate(value):
                to_print += (
                    str(item)
                    if not _special_attribute
                    else f"{getattr(item, _special_attribute)}"
                )
                if i + 1 != iterable_size:
                    to_print += ", "
        else:
            to_print += (
                f"{value}"
                if not _special_attribute
                else f"{getattr(value, _special_attribute)}"
            )
        if _new_line:
            to_print += "\n"
            self.in_new_line = True
        return to_print

    def print(
        self,
        value,
        *,
        _new_line=False,
        _is_iterable=False,
        _special_attribute=None,
        _use_visit=False,
    ):
        """
        outputs required value to target file.
        :param value: Value required to print.
        :param _new_line: End line with a \n.
        :param _is_iterable: Is the value iterable (list, tuple, etc...).
        :param _special_attribute: Special attribute that we need to print instead of value.
        :param _use_visit: should item be printed directly or use visit_class() method.
        :return: None.
        """
        if not _use_visit:
            to_print = self._prepare_line(
                value, _new_line, _is_iterable, _special_attribute
            )
            logging.debug(f"in print(), to_print='{to_print}'")
            self.current_line_len += len(to_print)
            self.current_line += to_print
            logging.debug(
                f"current line={self.current_line}, line length={self.current_line_len}"
            )
            if _new_line and self.current_line_len <= self.max_line:
                file.write(self.current_line)
                self.current_line_len = 0
                self.current_line = ""
            elif _new_line:  # Exceeded line limitation
                # TODO: Handle writing long lines properly
                self.check_line()

        elif _is_iterable and _use_visit:
            for i, item in enumerate(value):
                self.visit(item, new_line=False)
                if i + 1 != len(value):
                    self.print(", ")

    def check_line(self):
        """
        Checks if the current line exceeded the max length, initializes the needed
        variables to start a new line and calls the main node that starts the line.
        If the node supports checking for long lines, it will be handled well, the
        program will go into an endless recursion.
        :return: None
        """
        if self.current_line_len > self.max_line:
            logging.warning("Line exceeded limit")
            self._init_values_for_long_line()
            self.visit(self.starting_new_line_node, new_line=False)
            self.long_node = False

    def new_line(self, num=1):
        logging.debug(f"printing {num} new line")
        [self.print("", _new_line=True) for _ in range(num)]

    def visit_Module(self, node):
        logging.info("in visit_Module")
        for i, body_node in enumerate(node.body):
            self.starting_new_line_node = body_node
            if i == 0 and ast.get_docstring(node):  # Docstring
                self.visit_Constant(body_node.value, is_docstring=True)
            else:
                if i + 1 == len(node.body):
                    # Mark the last node in module.
                    self.last_node = True
                self.visit(body_node)
            if (
                i + 1 != len(node.body)
                and not isinstance(node.body[i], (_ast.FunctionDef, _ast.ClassDef))
                and isinstance(node.body[i + 1], (_ast.FunctionDef, _ast.ClassDef))
            ):
                # If the current node is not a definition node and the next node is a
                # definition node, add <vertical_definition_lines> empty lines.
                self.new_line(self.vertical_definition_lines)

    def visit_Import(self, node):
        """
        Implements import statements, prints each import in an independent line.
        :param node: _ast.Import node.
        :return: None
        """
        logging.info(f"in visit_Import")
        imports_list = node.names
        if self.multiple_imports:
            self.print("import ")
            for i, name in enumerate(imports_list):
                self.print(name.name)
                if i + 1 != len(imports_list):
                    self.print(", ")
            return

        for i, name in enumerate(imports_list):
            self.print(
                f"import {name.name}",
                _new_line=True if i + 1 != len(imports_list) else False,
            )

    def visit_ImportFrom(self, node):
        """
        Implements import from statements, prints all imports from specific library
        in a single line.
        :param node: _ast.ImportFrom node
        :return: None
        """
        logging.info(f"in visit_ImportFrom")
        import_list = node.names
        # Note that if the user wrote multiple import from statements using the same
        # library more than once, these import from lines won't be joined together as
        # the software should not change the order of the code.
        # TODO: Allow choosing whether to join multiple import from statements.
        self.print(f"from {node.module} import ")
        self.print(import_list, _is_iterable=True, _special_attribute="name")

    def visit_UnaryOp(self, node):
        """
        Implements the unary operators ["not, "~", "+", "-"].
        :param node: _ast.UnaryOp node.
        :return: None
        """
        ops = {_ast.Not: "not", ast.Invert: "~", ast.UAdd: "+", ast.USub: "-"}
        op = ops[type(node.op)]
        logging.info(f"in visit_UnaryOp, op={op}, operand={node.operand}")

        self.print(f"{op}")
        if isinstance(node.op, _ast.Not):
            self.print(" ")
        self.visit(node.operand, False)

    def visit_BinOp(self, node):
        """
        Implements the Binary operators.
        :param node: _ast.BinOp node.
        :return: None.
        """
        logging.info(
            f"in visit_BinOp, left={type(node.left).__name__}, "
            f"op={self.ar_ops[type(node.op)]}, right={type(node.right).__name__}"
        )
        first_recursive = False
        if self.long_node:
            # If the line length, print each operator in a new line.
            if self.first_long_node:  # Starting node of the sequence of inner nodes.
                self.print("(", _new_line=True)
                self.first_long_node = False
                self.change_indentation(4)
                first_recursive = True
            self.visit(node.left, new_line=False)
            self.new_line()
            self.print(f"{self.ar_ops[type(node.op)]} ")
            self.visit(node.right, new_line=False)
            if first_recursive:
                self.change_indentation(-4)
                self.new_line()
                self.print(")", _new_line=True)
            return
        self.visit(node.left, False)
        self.print(f" {self.ar_ops[type(node.op)]} ")
        self.visit(node.right, False)

    def visit_AugAssign(self, node):
        logging.info(
            f"in visit_AugAssign, target={node.target} op={self.ar_ops[type(node.op)]}, value={node.value}"
        )
        self.visit(node.target, new_line=False)
        self.print(f" {self.ar_ops[type(node.op)]}= ")
        self.visit(node.value, new_line=False)

    def visit_Constant(self, node, is_docstring=False):
        if is_docstring:
            logging.info(f"in visit_Constant, visiting docstring")
        else:
            logging.info(f"in visit_Constant, value={node.value}")
        if isinstance(node.value, str):
            self.print('"')
            if is_docstring:
                self.print('""')
        self.print(node.value)
        if isinstance(node.value, str):
            self.print('"')
            if is_docstring:
                self.print('""')
                self.new_line()

    def visit_Name(self, node):
        logging.info(f"in visit_Name, node.id={node.id}")
        self.print(node.id)

    def visit_Continue(self, node):
        logging.info(f"in visit_Continue")
        self.print("continue")

    def visit_Break(self, node):
        logging.info(f"in visit_Break")
        self.print("break")

    def visit_Delete(self, node):
        logging.info(f"in visit_Delete")
        self.print("del ")
        for i, target in enumerate(node.targets):
            self.visit(target, new_line=False)
            if i + 1 != len(node.targets):
                self.print(", ")

    def visit_BoolOp(self, node):
        op = "and" if isinstance(node.op, _ast.And) else "or"
        logging.info(f"in visit_BoolOp, op={op}, number_of_values={len(node.values)}")
        for i, value in enumerate(node.values):
            self.visit(value, new_line=False)
            if i + 1 != len(node.values):
                self.print(f" {op} ")

    def visit_List(self, node):
        logging.info(f"in visit_List")
        self.print("[")
        self.print(node.elts, _is_iterable=True, _use_visit=True)
        self.print("]")

    def visit_Dict(self, node):
        logging.info(f"in visit_Dict")
        self.print("{")
        self.new_line()
        with self:
            for key, value in zip(node.keys, node.values):
                self.visit(key, new_line=False)
                self.print(": ")
                self.visit(value, new_line=False)
                self.print(",")
                self.new_line()
        self.print("}")

    def visit_Tuple(self, node):
        logging.info(f"in visit_Tuple")
        self.print("(")
        self.print(node.elts, _is_iterable=True, _use_visit=True)
        self.print(")")

    def visit_Pass(self, node):
        logging.info(f"in visit_Pass")
        self.print("pass")

    def visit_Return(self, node):
        logging.info(f"in visit_Return")
        self.print("return")
        if node.value:
            self.print(" ")
            self.visit(node.value, new_line=False)

    def visit_Global(self, node):
        logging.info(f"in visit_Global")
        self.print("global ")
        self.print(node.names, _is_iterable=True)

    def visit_Nonlocal(self, node):
        logging.info(f"in visit_Nonlocal")
        self.print("nonlocal ")
        self.print(node.names, _is_iterable=True)

    def visit_NamedExpr(self, node):
        logging.info(f"in visit_NamedExpr")
        self.print("(")
        self.visit(node.target, new_line=False)
        self.print(f" := ")
        self.visit(node.value, new_line=False)
        self.print(")")

    def visit_Assign(self, node):
        logging.info(f"in visit_Assign")
        for target in node.targets:
            self.visit(target, False)
            self.print(" = ")
        self.visit(node.value, False)

    def visit_Compare(self, node):
        logging.info(f"in visit_Compare")
        ops = {
            _ast.Eq: "==",
            _ast.NotEq: "!=",
            _ast.Lt: "<",
            _ast.LtE: "<=",
            _ast.Gt: ">",
            _ast.GtE: ">=",
            _ast.Is: "is",
            _ast.IsNot: "is not",
            _ast.In: "in",
            _ast.NotIn: "not in",
        }
        self.visit(node.left, new_line=False)
        self.print(" ")
        for i, (op, comp) in enumerate(zip(node.ops, node.comparators)):
            self.print(f"{ops[type(op)]} ")
            self.visit(comp, new_line=False)
            if i + 1 != len(node.ops):
                self.print(" ")

    def visit_Subscript(self, node):
        logging.info(f"in visit_Subscript")
        self.visit(node.value, new_line=False)
        self.visit(node.slice, new_line=False)

    def visit_Index(self, node):
        logging.info(f"in visit_Index")
        self.print("[")
        self.visit(node.value, new_line=False)
        self.print("]")

    def visit_Slice(self, node):
        logging.info(f"in visit_Slice")
        self.print("[")
        if node.lower:
            self.visit(node.lower, new_line=False)
        self.print(":")
        if node.upper:
            self.visit(node.upper, new_line=False)
        if node.step:
            self.print(":")
            self.visit(node.step, new_line=False)
        self.print("]")

    def visit_Assert(self, node):
        logging.info(f"in visit_Assert")
        self.print("assert ")
        self.visit(node.test, new_line=False)
        if node.msg:
            self.print(", ")
            self.visit(node.msg, new_line=False)

    def visit_keyword(self, node):
        logging.info(f"in visit_keyword")
        if node.arg:
            self.print(
                f"{node.arg}" + (" = " if self.space_between_arguments else f"=")
            )
        else:
            self.print(f"**")
        self.visit(node.value, new_line=False)

    def visit_Attribute(self, node):
        logging.info(f"in visit_Attribute")
        self.visit(node.value, new_line=False)
        self.print(".")
        self.print(node.attr)

    def visit_Raise(self, node):
        logging.info(f"in visit_Raise")
        self.print("raise")
        if node.exc:
            self.print(" ")
            self.visit(node.exc, new_line=False)
        if node.cause:
            self.print(" from ")
            self.visit(node.cause, new_line=False)

    def visit_Try(self, node):
        logging.info(f"in visit_Try")
        self.print("try:", _new_line=True)
        with self:
            self._visit_list(node.body)
        for handle in node.handlers:
            self.visit(handle, new_line=False)
        if node.orelse:
            self.new_line()
            self.print("else:", _new_line=True)
            with self:
                self._visit_list(node.orelse)
        if node.finalbody:
            self.print("finally:", _new_line=True)
            with self:
                self._visit_list(node.finalbody, _new_line_at_finish=False)

    def visit_ExceptHandler(self, node):
        logging.info(f"in visit_ExceptHandler")
        self.print("except")
        if node.type:
            self.print(" ")
            self.visit(node.type, new_line=False)
        if node.name:
            self.print(f" as {node.name}")
        self.print(":", _new_line=True)
        with self:
            self._visit_list(node.body, _new_line_at_finish=False)

    def visit_Starred(self, node):
        logging.info(f"in visit_Starred")
        self.print("*")
        self.visit(node.value, new_line=False)

    def visit_arguments(self, node):
        logging.info(f"in visit_arguments")
        ordered_only_pos, ordered_args = Rewrite._ordered_pos_arg_default(
            node.posonlyargs, node.args, node.defaults
        )
        comma = "," + (" " if not self.long_node else "")
        if self.long_node:
            self.__enter__()
            self.new_line()
        for i, (key, value) in enumerate(ordered_only_pos.items()):
            self.print(key)
            if value:
                self.print(" = " if self.space_between_arguments else "=")
                self.visit(value[0], new_line=False)
            if i + 1 != len(ordered_only_pos):
                self.print(comma, _new_line=self.long_node)
            else:
                self.print(comma, _new_line=self.long_node)
                self.print("/", _new_line=self.long_node)
        if ordered_only_pos and (
            ordered_args or node.vararg or node.kwonlyargs or node.kwarg
        ):
            self.print(comma, _new_line=self.long_node)
        for i, (key, value) in enumerate(ordered_args.items()):
            self.print(key)
            if value:
                self.print(" = " if self.space_between_arguments else "=")
                self.visit(value[0], new_line=False)
            if (
                i + 1 != len(ordered_args)
                or node.vararg
                or node.kwonlyargs
                or node.kwarg
            ):
                self.print(comma, _new_line=self.long_node)
        if (ordered_args or ordered_only_pos) and (
            node.vararg or node.kwonlyargs or node.kwarg
        ):
            self.print("*")
        if node.vararg:
            if not (ordered_args or ordered_only_pos):
                self.print("*")
            self.print(f"{node.vararg.arg}")
        elif not (ordered_args or ordered_only_pos) and (node.kwonlyargs or node.kwarg):
            self.print("*")
            self.print(comma, _new_line=self.long_node)
        if (ordered_args or ordered_only_pos) and (node.kwonlyargs or node.kwarg):
            self.print(comma, _new_line=self.long_node)
        for i, item in enumerate(node.kwonlyargs):
            self.print(item.arg)
            if node.kw_defaults:
                if node.kw_defaults[0] is not None:
                    self.print(" = " if self.space_between_arguments else "=")
                    self.visit(node.kw_defaults[i], new_line=False)
            if i + 1 != len(node.kwonlyargs):
                self.print(comma, _new_line=self.long_node)
        if (
            ordered_args or ordered_only_pos or node.vararg or node.kwonlyargs
        ) and node.kwarg:
            self.print(comma, _new_line=self.long_node)
            self.print(f"**{node.kwarg.arg}")
        if self.long_node:
            self.__exit__(None, None, None)

    def visit_withitem(self, node):
        logging.info(f"in visit_withitem")
        self.visit(node.context_expr, new_line=False)
        if node.optional_vars:
            self.print(" as ")
            self.visit(node.optional_vars, new_line=False)

    def visit_With(self, node):
        logging.info(f"in visit_With")
        self.print("with ")
        for i, element in enumerate(node.items):
            self.visit(element, new_line=False)
            if i + 1 != len(node.items):
                self.print(", ")
        self.print(":", _new_line=True)
        with self:
            for i, element in enumerate(node.body):
                if i + 1 != len(node.body):
                    self.visit(element)
                else:
                    self.visit(element, new_line=False)

    def visit_FunctionDef(self, node):
        logging.info(f"in visit_FunctionDef")
        for decorator in node.decorator_list:
            self.print("@")
            self.visit(decorator)
        self.print(f"def {node.name}(")
        if node.args:
            self.visit(node.args, new_line=False)
        if self.long_node:
            self.new_line()
        self.print("):", _new_line=True)
        if self.long_node:
            # Note that if the function continues, the body will be printed twice.
            return
        self.last_body_node.append(self._get_latest_definition_node(node.body))

        with self:
            if ast.get_docstring(node):
                self.visit_Constant(node.body[0].value, is_docstring=True)
            for i, element in enumerate(node.body):
                if ast.get_docstring(node) and i == 0:
                    continue
                self.starting_new_line_node = element
                self.visit(element, new_line=i + 1 != len(node.body))
        if self.latest_class:
            return
        self.last_body_node.pop()
        self.print_new_lines_after_definition(node)

    def visit_ClassDef(self, node):
        logging.info(f"in visit_ClassDef")
        for decorator in node.decorator_list:
            self.print("@")
            self.visit(decorator)
        self.print(f"class {node.name}")
        if node.bases or node.keywords:
            self.print("(")
        if node.bases:
            for i, base in enumerate(node.bases):
                self.visit(base, new_line=False)
                if i + 1 != len(node.bases):
                    self.print(", ")
            if node.keywords:
                self.print(", ")
        if node.keywords:
            for i, keyword in enumerate(node.keywords):
                self.visit(keyword, new_line=False)
                if i + 1 != len(node.keywords):
                    self.print(", ")
        if node.bases or node.keywords:
            self.print(")")
        self.print(":", _new_line=True)
        self.last_body_node.append(self._get_latest_definition_node(node.body))
        with self:
            for i, element in enumerate(node.body):
                if ast.get_docstring(node) and i == 0:
                    self.visit_Constant(node.body[0].value, is_docstring=True)
                    continue
                if i + 1 == len(node.body):
                    self.latest_class = True
                self.starting_new_line_node = element
                self.visit(element, new_line=i + 1 != len(node.body))
                self.latest_class = False
        self.last_body_node.pop()
        self.print_new_lines_after_definition(node)

    def visit_If(self, node):
        logging.info(f"in visit_If")
        self.print("if ")
        self._block_flow(node=node, first_attr="test", is_if=True)

    def visit_While(self, node):
        logging.info(f"in visit_While")
        self.print("while ")
        self._block_flow(node=node, first_attr="test")

    def visit_For(self, node):
        logging.info(f"in visit_For")
        self.print("for ")
        self.visit(node.target, new_line=False)
        self.print(" in ")
        self._block_flow(node=node, first_attr="iter")

    def visit_Call(self, node):
        logging.info(f"in visit_Call")
        self.visit(node.func, new_line=False)
        self.print("(")
        for i, arg in enumerate(node.args):
            self.visit(arg, new_line=False)
            if i + 1 != len(node.args) or node.keywords:
                self.print(", ")
        for i, kwarg in enumerate(node.keywords):
            self.visit(kwarg, new_line=False)
            if i + 1 != len(node.keywords):
                self.print(", ")
        self.print(")")

    def visit_ListComp(self, node):
        logging.info(f"in visit_ListComp")
        self.print("[")
        self.visit(node.elt, new_line=False)
        for generator in node.generators:
            self.print(" for ")
            self.visit(generator, new_line=False)
        self.print("]")

    def visit_IfExp(self, node):
        logging.info(f"in visit_IfExp")
        self.visit(node.body, new_line=False)
        self.print(" if ")
        self.visit(node.test, new_line=False)
        self.print(" else ")
        self.visit(node.orelse, new_line=False)

    def visit_comprehension(self, node):
        logging.info(f"in visit_comprehension")
        self.visit(node.target, new_line=False)
        self.print(" in ")
        self.visit(node.iter, new_line=False)
        if node.ifs:
            for if_liner in node.ifs:
                self.print(" if ")
                self.visit(if_liner, new_line=False)

    def _block_flow(self, node, first_attr, is_if=False):
        node_attr = getattr(node, first_attr)
        self.visit(node_attr, new_line=False)
        self.print(":", _new_line=True)
        with self:
            for i, element in enumerate(node.body):
                if i + 1 != len(node.body):
                    self.visit(element)
                else:
                    self.visit(element, False)
        if node.orelse:
            self.new_line()
            if is_if and type(node.orelse[0]) is _ast.If:
                self.print("el")
                self.visit(node.orelse[0], False)
            else:
                self.print("else:", _new_line=True)
                with self:
                    for i, element in enumerate(node.orelse):
                        if i + 1 != len(node.orelse):
                            self.visit(element)
                        else:
                            self.visit(element, False)

    def _visit_list(self, nodes_list, *, _new_line_at_finish=True):
        for i, node in enumerate(nodes_list):
            self.visit(node, new_line=i + 1 != len(nodes_list) or _new_line_at_finish)

    @staticmethod
    def _ordered_pos_arg_default(pos_only_args, args, defaults):
        assert len(pos_only_args) + len(args) >= len(defaults), (
            len(pos_only_args),
            len(args),
            len(defaults),
        )
        total_args_size = len(pos_only_args) + len(args)
        default_size = len(defaults)
        ordered_only_pos = OrderedDict()
        ordered_args = OrderedDict()
        pos_defaults = 0
        for i, pos_only_arg in enumerate(pos_only_args):
            if i >= total_args_size - default_size:
                ordered_only_pos[pos_only_arg.arg] = [
                    defaults[i - total_args_size + default_size]
                ]
                pos_defaults += 1
            else:
                ordered_only_pos[pos_only_arg.arg] = []
        if pos_defaults:
            for i, arg in enumerate(args):
                ordered_args[arg.arg] = [defaults[i + pos_defaults]]
        else:  # No default argument has been used yet.
            total_defaults = len(args) - len(defaults)
            for i, arg in enumerate(args):
                if i >= total_defaults:
                    ordered_args[arg.arg] = [defaults[i - total_defaults]]
                else:
                    ordered_args[arg.arg] = []
        return ordered_only_pos, ordered_args

    def change_indentation(self, value):
        self.indentation += value

    def _init_values_for_long_line(self):
        """
        Helper function to initialize all the needed variables in case of a long line.
        :return:
        """
        self.current_line_len = 0
        self.current_line = ""
        self.in_new_line = True
        self.long_node = True
        self.first_long_node = True

    @staticmethod
    def _get_latest_definition_node(body):
        """
        Detects and returns the last function/class definition in a list of nodes and
        whether the function/class definition is the last item in the body.
        :param body: list of nodes.
        :return: Tuple containing the last definition and whether its the last item in
                 body.
        """
        for i, node in enumerate(reversed(body)):
            if isinstance(node, (_ast.ClassDef, _ast.FunctionDef)):
                return node, i == 0
        return None, None

    def print_new_lines_after_definition(self, node):
        if not (
            self.last_node
            or (
                self.nested_scope
                and (node == self.last_body_node[-1][0] and self.last_body_node[-1][1])
            )
        ):
            self.new_line(
                self.nested_lines
                if self.nested_scope
                else self.vertical_definition_lines
            )


def reformat(visitor):
    """
    Rewrites all the given files.
    :param visitor: Rewrite() object, containing all the necessary configurations.
    :return: 0 if no changes are needed, 1 otherwise.
    """
    global file
    for target_file in visitor.files:
        with open(target_file) as f:
            # Parse the python files and extract the AST.
            parsed = ast.parse(f.read(), target_file)
        if visitor.directory is not None:
            # When using a directory, reformat the original file.
            file = open(target_file, "+r")
        else:
            # When using direct file, dump the newly reformatted code in
            # temporary file
            # TODO Change this behaviour before release
            reformatted_file = "modified_file.py"
            file = open(reformatted_file, "a")
        try:
            # Rewrite the code by using the AST.
            visitor.visit(parsed)
        # Files with SyntaxErrors cannot be reformatted as parsing the AST tree of
        # these files is not possible.
        except SyntaxError as e:
            raise e
        except RecursionError:
            message = (
                "maximum recursion depth exceeded while calling a Python object"
                ", check maximum line length"
            )
            raise NoSolutionError(message)

        file.close()
        if visitor.check_only:
            exit(not filecmp.cmp(target_file, "modified_file.py"))
        # Delete the file in case we're in pytest environment
        elif "PYTEST_CURRENT_TEST" not in os.environ:
            copyfile(reformatted_file, target_file)
            os.remove(reformatted_file)
    return 0


def rewrite(*argv):
    visitor = Rewrite()
    configurations = _conf.Conf()
    # Set the configurations according to the configuration file
    configurations.set_configurations(visitor)
    # Parse the arguments that were given by the command line.
    # Note that these arguments override the default configuration file conf.txt
    # Note that if a configuration file was given (aside from the default conf.txt
    # file), it will override the configurations that were given by the command line
    # arguments.
    configurations.parse_arguments(argv, visitor)
    # If a directory was given, find all the files that need to be formatted in the
    # directory and its sub-directories.
    # Note that these files does not have to be Python files only since additional
    # suffixes could be given by the user.
    if visitor.directory is not None:
        _search.walk(
            root_directory=visitor.directory,
            files_list=visitor.files,
            suffixes=visitor.allowed_suffixes,
        )
    else:
        visitor.files = [visitor.target_file]
    # Return the exit code this is useful for CI/CD procedure, and particularly when
    # using --check-only argument.
    return reformat(visitor)


file = None
