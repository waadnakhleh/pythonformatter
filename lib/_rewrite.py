import ast
import _ast
from _ast import AST
from collections import OrderedDict


def iter_fields(node):
    """
    Yield a tuple of ``(fieldname, value)`` for each field in ``node._fields``
    that is present on *node*.
    """
    for field in node._fields:
        try:
            yield field, getattr(node, field)
        except AttributeError:
            pass


class Rewrite(ast.NodeVisitor):
    def __init__(self):
        self.indentation = 0
        self.in_new_line = True
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

    def __enter__(self):
        self.indentation += 4

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.indentation -= 4

    def visit(self, node, new_line=True):
        """
        Visit a node, this overrides NodeVisitor visit method as we need to
        start a new line between each body element.
        """
        method = 'visit_' + node.__class__.__name__
        visitor = getattr(self, method, self.generic_visit)
        visitor_ = visitor(node)
        if new_line and not isinstance(node, ast.Module):
            self.new_line()
        return visitor_

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        for field, value in iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, AST):
                        if isinstance(node, _ast.Module):
                            self.visit(item)
                        else:
                            self.visit(item, False)
            elif isinstance(value, AST):
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
        if self.in_new_line:
            to_print = " " * self.indentation  # Prepare indentation first.
            self.in_new_line = False
        if _is_iterable:
            assert hasattr(value, "__iter__")  # Make sure the item is iterable.
            iterable_size = len(value)
            for i, item in enumerate(value):
                to_print += str(item) if not _special_attribute else f"{getattr(item, _special_attribute)}"
                if i + 1 != iterable_size:
                    to_print += ", "
        else:
            to_print += f"{value}" if not _special_attribute else f"{getattr(value, _special_attribute)}"
        if _new_line:
            to_print += "\n"
            self.in_new_line = True
        return to_print

    def print(self, value, *, _new_line=False, _is_iterable=False, _special_attribute=None, _use_visit=False):
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
            to_print = self._prepare_line(value, _new_line, _is_iterable, _special_attribute)
            file.write(to_print)
        elif _is_iterable and _use_visit:
            for i, item in enumerate(value):
                self.visit(item, new_line=False)
                if i + 1 != len(value):
                    self.print(", ")

    def new_line(self):
        self.print("", _new_line=True)

    def visit_Import(self, node):
        imports_list = node.names
        for i, name in enumerate(imports_list):
            self.print(f"import {name.name}", _new_line=True if i + 1 != len(imports_list) else False)

    def visit_ImportFrom(self, node):
        import_list = node.names
        self.print(f"from {node.module} import ")
        self.print(import_list, _is_iterable=True, _special_attribute="name")

    def visit_UnaryOp(self, node):
        ops = {_ast.Not: "not", ast.Invert: "~", ast.UAdd: "+", ast.USub: "-"}
        self.print(f"{ops[type(node.op)]}")
        if isinstance(node.op, _ast.Not):
            self.print(" ")
        self.visit(node.operand, False)

    def visit_BinOp(self, node):
        self.visit(node.left, False)
        self.print(f" {self.ar_ops[type(node.op)]} ")
        self.visit(node.right, False)

    def visit_AugAssign(self, node):
        self.visit(node.target, new_line=False)
        self.print(f" {self.ar_ops[type(node.op)]}= ")
        self.visit(node.value, new_line=False)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            self.print('"')
        self.print(node.value)
        if isinstance(node.value, str):
            self.print('"')

    def visit_Name(self, node):
        self.print(node.id)

    def visit_Continue(self, node):
        self.print("continue")

    def visit_Break(self, node):
        self.print("break")

    def visit_BoolOp(self, node):
        op = "and" if isinstance(node.op, _ast.And) else "or"
        for i, value in enumerate(node.values):
            self.visit(value, new_line=False)
            if i + 1 != len(node.values):
                self.print(f" {op} ")

    def visit_List(self, node):
        self.print("[")
        self.print(node.elts, _is_iterable=True, _use_visit=True)
        self.print("]")

    def visit_Tuple(self, node):
        self.print("(")
        self.print(node.elts, _is_iterable=True, _use_visit=True)
        self.print(")")

    def visit_Pass(self, node):
        self.print("pass")

    def visit_Return(self, node):
        self.print("return ")
        self.visit(node.value, new_line=False)

    def visit_NamedExpr(self, node):
        self.print("(")
        self.visit(node.target, new_line=False)
        self.print(f" := ")
        self.visit(node.value, new_line=False)
        self.print(")")

    def visit_Assign(self, node):
        for target in node.targets:
            self.visit(target, False)
            self.print(" = ")
        self.visit(node.value, False)

    def visit_Compare(self, node):
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

    def visit_Assert(self, node):
        self.print("assert ")
        self.visit(node.test, new_line=False)
        if node.msg:
            self.print(", ")
            self.visit(node.msg, new_line=False)

    def visit_keyword(self, node):
        if node.arg:
            self.print(f"{node.arg}=")
        else:
            self.print(f"**")
        self.visit(node.value, new_line=False)

    def visit_Starred(self, node):
        self.print("*")
        self.visit(node.value, new_line=False)

    def visit_arguments(self, node):
        ordered_only_pos, ordered_args = Rewrite._ordered_pos_arg_default(node.posonlyargs, node.args, node.defaults)
        for i, (key, value) in enumerate(ordered_only_pos.items()):
            self.print(key)
            if value:
                self.print(f"=")
                self.visit(value[0], new_line=False)
            if i + 1 != len(ordered_only_pos):
                self.print(", ")
            else:
                self.print(", /")
        if ordered_only_pos and (ordered_args or node.vararg or node.kwonlyargs or node.kwarg):
            self.print(", ")
        for i, (key, value) in enumerate(ordered_args.items()):
            self.print(key)
            if value:
                self.print(f"=")
                self.visit(value[0], new_line=False)
            if i + 1 != len(ordered_args) or node.vararg or node.kwonlyargs or node.kwarg:
                self.print(", ")
        if (ordered_args or ordered_only_pos) and (node.vararg or node.kwonlyargs or node.kwarg):
            self.print("*")
        if node.vararg:
            if not (ordered_args or ordered_only_pos):
                self.print("*")
            self.print(f"{node.vararg.arg}")
        elif not (ordered_args or ordered_only_pos) and (node.kwonlyargs or node.kwarg):
            self.print("*, ")
        if (ordered_args or ordered_only_pos) and (node.kwonlyargs or node.kwarg):
            self.print(", ")
        for i, item in enumerate(node.kwonlyargs):
            self.print(item.arg)
            if node.kw_defaults:
                if node.kw_defaults[0] is not None:
                    self.print("=")
                    self.visit(node.kw_defaults[i], new_line=False)
            if i + 1 != len(node.kwonlyargs):
                self.print(", ")
        if (ordered_args or ordered_only_pos or node.vararg or node.kwonlyargs) and node.kwarg:
            self.print(f", **{node.kwarg.arg}")

    def visit_FunctionDef(self, node):
        for decorator in node.decorator_list:
            self.print("@")
            self.visit(decorator)
        self.print(f"def {node.name}(")
        if node.args:
            self.visit(node.args, new_line=False)
        self.print("):", _new_line=True)
        with self:
            for element in node.body:
                self.visit(element)
        self.new_line()

    def visit_If(self, node):
        self.print("if ")
        self.visit(node.test, new_line=False)
        self.print(":", _new_line=True)
        with self:
            for i, element in enumerate(node.body):
                if i + 1 != len(node.body):
                    self.visit(element)
                else:
                    self.visit(element, False)
        if node.orelse:
            self.new_line()
            if type(node.orelse[0]) is _ast.If:
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

    def visit_While(self, node):
        self.print("while ")
        self.visit(node.test, new_line=False)
        self.print(":", _new_line=True)
        with self:
            for i, element in enumerate(node.body):
                if i + 1 != len(node.body):
                    self.visit(element)
                else:
                    self.visit(element, False)
        if node.orelse:
            self.new_line()
            self.print("else:", _new_line=True)
            with self:
                for i, element in enumerate(node.orelse):
                    if i + 1 != len(node.orelse):
                        self.visit(element)
                    else:
                        self.visit(element, False)

    def visit_For(self, node):
        # classFor(target, iter, body, orelse, type_comment)
        self.print("for ")
        self.visit(node.target, new_line=False)
        self.print(" in ")
        self.visit(node.iter, new_line=False)
        self.print(":", _new_line=True)
        with self:
            for i, element in enumerate(node.body):
                if i + 1 != len(node.body):
                    self.visit(element)
                else:
                    self.visit(element, False)
        if node.orelse:
            self.new_line()
            self.print("else:", _new_line=True)
            with self:
                for i, element in enumerate(node.orelse):
                    if i + 1 != len(node.orelse):
                        self.visit(element)
                    else:
                        self.visit(element, False)

    def visit_Call(self, node):
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

    @staticmethod
    def _ordered_pos_arg_default(pos_only_args, args, defaults):
        assert len(pos_only_args) + len(args) >= len(defaults), (len(pos_only_args), len(args),len(defaults))
        total_args_size = len(pos_only_args) + len(args)
        default_size = len(defaults)
        ordered_only_pos = OrderedDict()
        ordered_args = OrderedDict()
        pos_defaults = 0
        for i, pos_only_arg in enumerate(pos_only_args):
            if i >= total_args_size - default_size:
                ordered_only_pos[pos_only_arg.arg] = [defaults[i - total_args_size + default_size]]
                pos_defaults += 1
            else:
                ordered_only_pos[pos_only_arg.arg] = []
        if pos_defaults:
            for i, arg in enumerate(args):
                ordered_args[arg.arg] = [defaults[i+pos_defaults]]
        else:  # No default argument has been used yet.
            total_defaults = len(args) - len(defaults)
            for i, arg in enumerate(args):
                if i >= total_defaults:
                    ordered_args[arg.arg] = [defaults[i-total_defaults]]
                else:
                    ordered_args[arg.arg] = []
        return ordered_only_pos, ordered_args


def rewrite(file_name: str):
    global file
    file = open("modified_file.py", "a")
    with open(file_name) as f:
        try:
            parsed = ast.parse(f.read(), file_name)  # the AST of the .py file
            Rewrite().visit(parsed)
        except SyntaxError as e:
            raise e
        file.close()


file = None
