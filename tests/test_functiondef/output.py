from pytest import fixture
@fixture
def my_new_func(a, f="fuck", /, b="2", c="TEST", *args, testy, test, **kwargs):
    print("Hello, world!")
    return 10


def hello(name):
    print("hello ", name)


def another_one(*args, **kwargs):
    pass


def yet_another(pos_only_arg, /):
    pass


def another_function(a=10, b=200, *, c=30):
    pass


def foo(*, test="foo", **kwargs):
    pass


def bar(pos_only_arg, /, *, test):
    pass


def foo_bar(arg1="quick brown fox", *, arg2=False):
    pass


my_new_func(10, 3, d=3)
