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
        """
        Initializes all the object's variables.
        """
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
            if isinstance(value, _ast.AST):
                self.visit(value, False)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, _ast.AST):
                        self.visit(item, False)

    def visit_Expr(self, node):
        """
        Handles Expressions.
        When an expression, such as function call appears as a statement by itself, meaning
        that its return value is not stored or used, it is wrapped in an expression node.
        The main purpose of this function is to handle the nodes that exceeds the
        maximum line length
        :param node: _ast.Expr Node
        :return: None
        """
        for field, value in ast.iter_fields(node):
            if isinstance(value, _ast.AST):
                value.exceeds_maximum_length = node.exceeds_maximum_length
                self.visit(value, False)
                value.exceeds_maximum_length = False
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, _ast.AST):
                        value.exceeds_maximum_length = node.exceeds_maximum_length
                        self.visit(item, False)
                        value.exceeds_maximum_length = False

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
            self.starting_new_line_node.exceeds_maximum_length = False
            self.long_node = False

    def new_line(self, num=1):
        """Prints <num> new line(s)"""
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
        """
        Implements the augmented assignments (e.g., a += 10)
        :param node: _ast.AugAssign node
        :return: None
        """
        logging.info(
            f"in visit_AugAssign, target={node.target} op={self.ar_ops[type(node.op)]}, value={node.value}"
        )
        self.visit(node.target, new_line=False)
        self.print(f" {self.ar_ops[type(node.op)]}= ")
        self.visit(node.value, new_line=False)

    def visit_Constant(self, node, is_docstring=False):
        """
        Implements the Constants.
        Note that the constants could be from multiple types like str, int.
        Note that the constant could be a docstring.
        :param node: _ast.Constant.
        :param is_docstring: True if the constant is a docstring false otherwise.
        :return: None
        """
        if is_docstring:
            logging.info(f"in visit_Constant, visiting docstring")
        else:
            logging.info(f"in visit_Constant, value={node.value}")
        if isinstance(node.value, str) and not is_docstring:
            # If the constant is a string, add quotes as a prefix.
            # If the code contains double quotes, use single quotes.
            self.print('"' if '"' not in node.value else "'")
        elif is_docstring:
            # If the constant is a docstring, add triple quotes as a prefix.
            self.print('"""')
        self.print(node.value)
        if isinstance(node.value, str) and not is_docstring:
            # If the constant is a string, add quotes as a suffix.
            # If the code contains double quotes, use single quotes.
            self.print('"' if '"' not in node.value else "'")
        elif is_docstring:
            # If the constant is a docstring, add triple quotes as a suffix.
            self.print('"""')
            self.new_line()

    def visit_Name(self, node):
        """
        Implements name (identifiers).
        :param node: _ast.Name.
        :return: None.
        """
        logging.info(f"in visit_Name, node.id={node.id}")
        self.print(node.id)

    def visit_Continue(self, node):
        """
        Implements Continue.
        :param node: _ast.Continue.
        :return: None.
        """
        logging.info(f"in visit_Continue")
        self.print("continue")

    def visit_Break(self, node):
        """
        Implements break.
        :param node: _ast.Break.
        :return: None.
        """
        logging.info(f"in visit_Break")
        self.print("break")

    def visit_Delete(self, node):
        """
        Implements Delete.
        :param node: _ast.Delete.
        :return: None
        """
        logging.info(f"in visit_Delete")
        self.print("del ")
        for i, target in enumerate(node.targets):
            self.visit(target, new_line=False)
            if i + 1 != len(node.targets):
                self.print(", ")

    def visit_BoolOp(self, node):
        """
        Implements the boolean operators "and" and "or".
        :param node: _ast.BoolOp.
        :return: None.
        """
        assert type(node.op) in [_ast.And, _ast.Or]
        op = "and" if isinstance(node.op, _ast.And) else "or"
        logging.info(f"in visit_BoolOp, op={op}, number_of_values={len(node.values)}")
        for i, value in enumerate(node.values):
            self.visit(value, new_line=False)
            if i + 1 != len(node.values):
                self.print(f" {op} ")

    def visit_List(self, node):
        """
        Implements Lists.
        :param node: _ast.List.
        :return: None
        """
        logging.info(f"in visit_List")
        self.print("[")
        self.print(node.elts, _is_iterable=True, _use_visit=True)
        self.print("]")

    def visit_Set(self, node):
        """
        Implements Sets.
        :param node: _ast.Set.
        :return: None
        """
        logging.info(f"in visit_Set")
        self.print("{")
        self.print(node.elts, _is_iterable=True, _use_visit=True)
        self.print("}")

    def visit_Dict(self, node):
        """
        Implements Dictionaries.
        :param node: _ast.Dict.
        :return: None
        """
        logging.info(f"in visit_Dict")
        self.print("{")
        self.new_line()
        # TODO small dictionaries should not use multiple lines.
        with self:
            for key, value in zip(node.keys, node.values):
                self.visit(key, new_line=False)
                self.print(": ")
                self.visit(value, new_line=False)
                self.print(",")
                self.new_line()
        self.print("}")

    def visit_Tuple(self, node):
        """
        Implements Tuples.
        :param node: _ast.Tuple.
        :return: None
        """
        logging.info(f"in visit_Tuple")
        self.print("(")
        self.print(node.elts, _is_iterable=True, _use_visit=True)
        self.print(")")

    def visit_Pass(self, node):
        """
        Implements Pass.
        :param node: _ast.Pass.
        :return: None
        """
        logging.info(f"in visit_Pass")
        self.print("pass")

    def visit_Return(self, node):
        """
        Implements Return
        :param node: _ast.Return.
        :return: None
        """
        logging.info(f"in visit_Return")
        self.print("return")
        if node.value:
            self.print(" ")
            self.visit(node.value, new_line=False)

    def visit_Global(self, node):
        """
        Implements Global
        :param node: _ast.Global.
        :return: None
        """
        logging.info(f"in visit_Global")
        self.print("global ")
        self.print(node.names, _is_iterable=True)

    def visit_Nonlocal(self, node):
        """
        Implements Nonlocal
        :param node: _ast.Nonlocal.
        :return: None
        """
        logging.info(f"in visit_Nonlocal")
        self.print("nonlocal ")
        self.print(node.names, _is_iterable=True)

    def visit_NamedExpr(self, node):
        """
        Implements named expressions.
        Note: Named expressions were introduced in Python 3.8.
        :param node: _ast.NamedExpr.
        :return: None
        """
        logging.info(f"in visit_NamedExpr")
        self.print("(")
        self.visit(node.target, new_line=False)
        self.print(f" := ")
        self.visit(node.value, new_line=False)
        self.print(")")

    def visit_Assign(self, node):
        """
        Implements assignments.
        :param node: _ast.Assign.
        :return: None
        """
        logging.info(f"in visit_Assign")
        for target in node.targets:
            self.visit(target, False)
            self.print(" = ")
        self.visit(node.value, False)

    def visit_Compare(self, node):
        """
        Implements comparisons.
        :param node: _ast.Compare.
        :return: None
        """
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
        # Note that node.ops contains the operators as instances of _ast.op_type,
        # therefor, they must be casted to a string using the previously declared ops
        # dictionary.
        # Note that the node.comparators contains the all operands of the comparison
        # except for the first left hand side operand, node.comparators could store
        # multiple operands when using chained comparisons.
        for i, (op, comp) in enumerate(zip(node.ops, node.comparators)):
            self.print(f"{ops[type(op)]} ")
            self.visit(comp, new_line=False)
            if i + 1 != len(node.ops):
                self.print(" ")

    def visit_Subscript(self, node):
        """
        Implements Subscript.
        :param node: _ast.Subscript.
        :return: None
        """
        logging.info(f"in visit_Subscript")
        self.visit(node.value, new_line=False)
        self.visit(node.slice, new_line=False)

    def visit_Index(self, node):
        """
        Implements Indexing.
        :param node: _ast.Index.
        :return: None
        """
        logging.info(f"in visit_Index")
        self.print("[")
        self.visit(node.value, new_line=False)
        self.print("]")

    def visit_Slice(self, node):
        """
        Implements Slicing.
        When slicing, there are three optional options [lower:upper:step].
        :param node: _ast.Slice.
        :return: None
        """
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
        """
        Implements Assertions.
        :param node: _ast.Assert.
        :return: None
        """
        logging.info(f"in visit_Assert")
        self.print("assert ")
        self.visit(node.test, new_line=False)
        if node.msg:
            self.print(", ")
            self.visit(node.msg, new_line=False)

    def visit_keyword(self, node):
        """
        Implements keyword arguments.
        :param node: _ast.keyword.
        :return: None
        """
        logging.info(f"in visit_keyword")
        if node.arg:
            self.print(
                f"{node.arg}" + (" = " if self.space_between_arguments else f"=")
            )
        else:
            # Keyword argument containing all keyword arguments except for those
            # corresponding to a formal parameter.
            self.print(f"**")
        self.visit(node.value, new_line=False)

    def visit_Attribute(self, node):
        """
        Implements Attributes.
        :param node: _ast.Attribute.
        :return: None
        """
        logging.info(f"in visit_Attribute")
        self.visit(node.value, new_line=False)
        self.print(".")
        self.print(node.attr)

    def visit_Raise(self, node):
        """
        Implements Raise.
        :param node: _ast.Raise.
        :return: None
        """
        logging.info(f"in visit_Raise")
        self.print("raise")
        if node.exc:
            self.print(" ")
            self.visit(node.exc, new_line=False)
        if node.cause:
            self.print(" from ")
            self.visit(node.cause, new_line=False)

    def visit_Try(self, node):
        """
        Implements try, except, and finally.
        :param node: _ast.Try.
        :return: None
        """
        logging.info(f"in visit_Try")
        self.print("try:", _new_line=True)
        with self:
            # Try block
            self._visit_list(node.body)
        for handle in node.handlers:
            # Except handlers
            self.visit(handle, new_line=False)
        if node.orelse:
            # Handle else statements after except statements
            self.new_line()
            self.print("else:", _new_line=True)
            with self:
                # Else block
                self._visit_list(node.orelse)
        if node.finalbody:
            # Handle finally.
            self.print("finally:", _new_line=True)
            with self:
                # Finally block.
                self._visit_list(node.finalbody, _new_line_at_finish=False)

    def visit_ExceptHandler(self, node):
        """
        Implements except handler.
        :param node: _ast.ExceptHandler node.
        :return: None
        """
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
        """
        Implements starred nodes.
        :param node: _ast.Starred node.
        :return: None
        """
        logging.info(f"in visit_Starred")
        self.print("*")
        self.visit(node.value, new_line=False)

    def visit_arguments(self, node):
        """
        Handles function/class arguments.
        :param node: _ast.arguments node.
        :return: None
        """
        logging.info(f"in visit_arguments")
        # Get all the positional arguments ordered.
        ordered_only_pos, ordered_args = Rewrite._ordered_pos_arg_default(
            node.posonlyargs, node.args, node.defaults
        )
        # When the line length of the arguments exceeds the maximum line length spaces
        # after the commas should not be printed, instead, move to
        # a new line to print the next argument.
        comma = "," + (" " if not node.exceeds_maximum_length else "")
        if node.exceeds_maximum_length:
            # Add indentation in case the node exceeds the maximum line length.
            self.__enter__()
            self.new_line()
        for i, (key, value) in enumerate(ordered_only_pos.items()):
            self.print(key)
            if value:
                self.print(" = " if self.space_between_arguments else "=")
                self.visit(value[0], new_line=False)
            if i + 1 != len(ordered_only_pos):
                self.print(comma, _new_line=node.exceeds_maximum_length)
            else:
                self.print(comma, _new_line=node.exceeds_maximum_length)
                self.print("/", _new_line=node.exceeds_maximum_length)
        if ordered_only_pos and (
            ordered_args or node.vararg or node.kwonlyargs or node.kwarg
        ):
            self.print(comma, _new_line=node.exceeds_maximum_length)
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
                self.print(comma, _new_line=node.exceeds_maximum_length)
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
            self.print(comma, _new_line=node.exceeds_maximum_length)
        if (ordered_args or ordered_only_pos) and (node.kwonlyargs or node.kwarg):
            self.print(comma, _new_line=node.exceeds_maximum_length)
        for i, item in enumerate(node.kwonlyargs):
            self.print(item.arg)
            if node.kw_defaults:
                if node.kw_defaults[0] is not None:
                    self.print(" = " if self.space_between_arguments else "=")
                    self.visit(node.kw_defaults[i], new_line=False)
            if i + 1 != len(node.kwonlyargs):
                self.print(comma, _new_line=node.exceeds_maximum_length)
        if (
            ordered_args or ordered_only_pos or node.vararg or node.kwonlyargs
        ) and node.kwarg:
            self.print(comma, _new_line=node.exceeds_maximum_length)
            self.print(f"**{node.kwarg.arg}")
        if node.exceeds_maximum_length:
            self.__exit__(None, None, None)

    def visit_withitem(self, node):
        """
        Handles "with" items.
        :param node: _ast.withitem.
        :return: None
        """
        logging.info(f"in visit_withitem")
        self.visit(node.context_expr, new_line=False)
        if node.optional_vars:
            self.print(" as ")
            self.visit(node.optional_vars, new_line=False)

    def visit_With(self, node):
        """
        Implements "with" statement blocks.
        :param node: _ast.With.
        :return: None
        """
        logging.info(f"in visit_With")
        self.print("with ")
        for i, element in enumerate(node.items):
            # Visit with items.
            self.visit(element, new_line=False)
            if i + 1 != len(node.items):
                self.print(", ")
        self.print(":", _new_line=True)
        with self:
            # with block.
            for i, element in enumerate(node.body):
                self.visit(element, new_line=i + 1 != len(node.body))

    def visit_FunctionDef(self, node):
        """
        Handles function definitions.
        :param node: _ast.FunctionDef node.
        :return: None
        """
        logging.info(f"in visit_FunctionDef")
        # Handle function decorators.
        for decorator in node.decorator_list:
            self.print("@")
            self.visit(decorator)
        self.print(f"def {node.name}(")
        # Handle function arguments.
        if node.args:
            node.args.exceeds_maximum_length = node.exceeds_maximum_length
            self.visit(node.args, new_line=False)
        # If the function definition exceeds the maximum line length, a new line should
        # be dedicated for the closing parenthesis.
        if node.exceeds_maximum_length:
            self.new_line()
        self.print("):", _new_line=True)
        if node.exceeds_maximum_length:
            # Note that if the function continues, the body will be printed twice.
            return

        # Append to last_body_node the last definition node in the class's body.
        self.last_body_node.append(self._get_latest_definition_node(node.body))

        # Start new indentation in order to print the function's body.
        with self:
            # Print docstring if exists.
            if ast.get_docstring(node):
                self.visit_Constant(node.body[0].value, is_docstring=True)
            # Handle the rest of the function's body.
            for i, element in enumerate(node.body):
                if ast.get_docstring(node) and i == 0:
                    continue
                self.starting_new_line_node = element
                self.visit(element, new_line=i + 1 != len(node.body))
        if self.latest_class:
            return
        # Since we're done printing the function, we can remove the last last_body_node
        # element.
        self.last_body_node.pop()
        # Handle new lines after the definition is over.
        self.print_new_lines_after_definition(node)

    def visit_ClassDef(self, node):
        """
        Handles class definition nodes.
        :param node: _ast.ClassDef node.
        :return: None
        """
        logging.info(f"in visit_ClassDef")
        # Handle decorators if they exist.
        for decorator in node.decorator_list:
            self.print("@")
            self.visit(decorator)
        self.print(f"class {node.name}")
        # Handle node bases and keywords (e.g. baseclass or keyword like metaclass="").
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

        # Append to last_body_node the last definition node in the class's body.
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
        # Since we're done printing the class, we can remove the last last_body_node
        # element.
        self.last_body_node.pop()
        # Handle new lines after the definition is over.
        self.print_new_lines_after_definition(node)

    def visit_If(self, node):
        """
        Handles If statements.
        :param node: _ast.If node.
        :return: None.
        """
        logging.info(f"in visit_If")
        self.print("if ")
        self._block_flow(node=node, first_attr="test", is_if=True)

    def visit_While(self, node):
        """
        Handles while statements.
        :param node: _ast.While
        :return: None
        """
        logging.info(f"in visit_While")
        self.print("while ")
        self._block_flow(node=node, first_attr="test")

    def visit_For(self, node):
        """
        Handles for statements.
        :param node: _ast.For node.
        :return: None
        """
        logging.info(f"in visit_For")
        self.print("for ")
        self.visit(node.target, new_line=False)
        self.print(" in ")
        self._block_flow(node=node, first_attr="iter")

    def visit_Call(self, node):
        """
        Handles function calls.
        :param node: _ast.Call node.
        :return: None
        """
        logging.info(f"in visit_Call")
        # Visit the function identifier node.
        comma = ","
        comma += "" if node.exceeds_maximum_length else " "
        self.visit(node.func, new_line=False)
        self.print("(")
        # Handle the function argument.
        if node.exceeds_maximum_length:
            # Start a new line.
            self.new_line()
            # Open new scope.
            self.__enter__()
        for i, arg in enumerate(node.args):
            self.visit(arg, new_line=False)
            if i + 1 != len(node.args) or node.keywords:
                self.print(comma, _new_line=node.exceeds_maximum_length)
        for i, kwarg in enumerate(node.keywords):
            self.visit(kwarg, new_line=False)
            if i + 1 != len(node.keywords):
                self.print(comma, _new_line=node.exceeds_maximum_length)
        if node.exceeds_maximum_length:
            # The closing parentheses must be on an independent line.
            self.new_line()
            # Close scope.
            self.__exit__(None, None, None)
        self.print(")", _new_line=node.exceeds_maximum_length)

    def visit_ListComp(self, node):
        """
        Handles list comprehensions.
        :param node: _ast.ListComp.
        :return: None
        """
        logging.info(f"in visit_ListComp")
        self.print("[")
        self.visit(node.elt, new_line=False)
        for generator in node.generators:
            # Note that a list comprehension usage could contain multiple ifs.
            self.print(" for ")
            self.visit(generator, new_line=False)
        self.print("]")

    def visit_IfExp(self, node):
        """
        Handle if expressions that are not followed by a block, e.g. "a" if b else "c".
        :param node: _ast.IfExp
        :return: None
        """
        logging.info(f"in visit_IfExp")
        self.visit(node.body, new_line=False)
        self.print(" if ")
        self.visit(node.test, new_line=False)
        self.print(" else ")
        self.visit(node.orelse, new_line=False)

    def visit_comprehension(self, node):
        """
        Handle comprehensions.
        :param node: _ast.comprehension node.
        :return: None
        """
        logging.info(f"in visit_comprehension")
        self.visit(node.target, new_line=False)
        self.print(" in ")
        self.visit(node.iter, new_line=False)
        if node.ifs:
            # Handle "if" statement if node contains ifs.
            for if_liner in node.ifs:
                self.print(" if ")
                self.visit(if_liner, new_line=False)

    def _block_flow(self, node, first_attr, is_if=False):
        """
        Helper function to handle If/While/For blocks.
        :param node: One of _ast.If, _ast.While, _ast.For node.
        :param first_attr: the first attributes name, "iter" if the node is an _ast.For
                            node, else "test".
        :param is_if: True if node is _ast.if node.
        :return: None
        """
        # Get the node of the first attribute.
        node_attr = getattr(node, first_attr)
        self.visit(node_attr, new_line=False)
        self.print(":", _new_line=True)
        # Open new indentation.
        with self:
            # Visit all the the nodes body block.
            for i, element in enumerate(node.body):
                if i + 1 != len(node.body):
                    self.visit(element)
                else:
                    self.visit(element, False)
        if node.orelse:
            # Handle else statement blocks if the node has an else block.
            self.new_line()
            if is_if and type(node.orelse[0]) is _ast.If:
                self.print("el")
                # Note that the statement should be an elif statement.
                self.visit(node.orelse[0], False)
            else:
                self.print("else:", _new_line=True)
                # Handle the else block
                with self:
                    for i, element in enumerate(node.orelse):
                        if i + 1 != len(node.orelse):
                            self.visit(element)
                        else:
                            self.visit(element, False)

    def _visit_list(self, nodes_list, *, _new_line_at_finish=True):
        """
        Calls visit() for each node in a list.
        When calling visit(), new_line argument will be always True except for the
        last node unless specified otherwise.
        :param nodes_list: List of nodes
        :param _new_line_at_finish: Should new line be printed when visiting the last
                                    node.
        :return: None
        """
        for i, node in enumerate(nodes_list):
            self.visit(node, new_line=i + 1 != len(nodes_list) or _new_line_at_finish)

    @staticmethod
    def _ordered_pos_arg_default(pos_only_args, args, defaults):
        """
        Orders the positional arguments (both positional only arguments and positional
        arguments in two ordered dictionaries, the dictionary's key is the arguments
        name and the value is the default value, in case the argument does not have a
        default value, the value will be empty.
        :param pos_only_args: positional only arguments
        :param args: positional arguments
        :param defaults: list containing default values for all positional arguments
        :return: Two ordered dictionaries containing the arguments and their default
                 value if existed.
        """
        # the arguments with default values that are stored in defaults are duplicated,
        # positional only arguments and positional arguments with default values are
        # stored in 'defaults' and one of ('pos_only_args', 'args).
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
        # Iterate over the positional only arguments since they must be written first.
        for i, pos_only_arg in enumerate(pos_only_args):
            # The last len(default) arguments have a default value.
            if i >= total_args_size - default_size:
                ordered_only_pos[pos_only_arg.arg] = [
                    defaults[i - total_args_size + default_size]
                ]
                pos_defaults += 1
            else:
                # Arguments does not have a default value
                ordered_only_pos[pos_only_arg.arg] = []
        if pos_defaults:
            # If there is at least on positional only argument that have a default
            # value, then all of the "regular" positional arguments have default
            # values.
            for i, arg in enumerate(args):
                ordered_args[arg.arg] = [defaults[i + pos_defaults]]
        else:
            # No default argument has been used yet.
            total_defaults = len(args) - len(defaults)
            for i, arg in enumerate(args):
                # The last len(default) arguments have a default value.
                if i >= total_defaults:
                    ordered_args[arg.arg] = [defaults[i - total_defaults]]
                else:
                    # The argument does not have a default value.
                    ordered_args[arg.arg] = []
        return ordered_only_pos, ordered_args

    def change_indentation(self, value):
        """
        Changes the current indentation
        :param value: Value of the indentation, must be multiple of 4
        :return: None
        """
        assert not value % 4, "Indentation error"
        self.indentation += value

    def cleanup(self):
        """
        Resets all the necessary variables in order to start reformatting again.
        :return: None
        """
        self.current_line_len = 0
        self.current_line = ""
        self.first_long_node = False
        self.indentation = 0
        self.in_new_line = True
        self.last_body_node = []
        self.last_node = False
        self.latest_class = False
        self.long_node = False
        self.nested_scope = 0

    def _init_values_for_long_line(self):
        """
        Helper function to initialize all the needed variables in case of a long line.
        :return:
        """
        self.starting_new_line_node.exceeds_maximum_length = True
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
        """
        A helper function to decide how many lines are printed after function/class
        definition.
        :param node: definition node.
        :return: None
        """
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


class NodeAttributes(ast.NodeVisitor):
    def visit(self, node):
        """Visit a node."""
        setattr(node, "exceeds_maximum_length", False)
        method = "visit_" + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        return visitor(node)


def reformat(visitor):
    """
    Rewrites all the given files.
    :param visitor: Rewrite() object, containing all the necessary configurations.
    :return: 0 if no changes are needed, 1 otherwise.
    """
    global file
    attribute_setter = NodeAttributes()
    modified_file = "modified_file.py"
    changed_files = []
    for target_file in visitor.files:
        with open(target_file) as f:
            # Parse the python files and extract the AST.
            parsed = ast.parse(f.read(), target_file)

        # Add necessary attributes to the AST nodes.
        attribute_setter.visit(parsed)

        # Write the changes to an external file.
        file = open(modified_file, "w+")
        try:
            # Rewrite the code by using the AST.
            visitor.visit(parsed)
        # Files with SyntaxErrors cannot be reformatted as parsing the AST tree of
        # these files is not possible.
        except SyntaxError as e:
            raise e
        # Recursion Error usually happens when the system fails to format the file.
        # An example of this would be a maximum line length that exceeds an
        # identifier's name.
        except RecursionError:
            message = (
                "maximum recursion depth exceeded while calling a Python object"
                ", check maximum line length"
            )
            raise NoSolutionError(message)
        # Finish writing to the file
        file.close()
        if visitor.check_only:
            # Compare the external file with the original file.
            exit(not filecmp.cmp(target_file, modified_file))
        # When in pytest environment, the system should not change the original files
        # content.
        if "PYTEST_CURRENT_TEST" not in os.environ:
            if not filecmp.cmp(modified_file, target_file):
                # If the file has changed, add it to changed_files
                changed_files.append(target_file)
            # Move the external file's content to the original file
            copyfile(modified_file, target_file)
            # Remove the external file.
            os.remove(modified_file)
        # Reset all the object's attributes to their default value.
        visitor.cleanup()
        # Print summary
        if changed_files:
            was_or_were = "was" if len(changed_files) == 1 else "were"
            print(f"{len(changed_files)} {was_or_were} changed")
            print("\nThe following files were changed:")
            for changed_file in changed_files:
                print(changed_file)
        print("No files were changed")
    return 0


def rewrite(*argv):
    """
    Handles the rewriting process by parsing the arguments and configurations, gathers
    the path of the files that need to be formatted and rewrites them.
    :param argv: The command line arguments provided by the user
    :return: 0 if the code is formatted, 1 otherwise
    """
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
