class Ages:
    def __init__(self, age):
        self.age = age

    def __str__(self):
        return str(self.age)

    def __add__(self, other):
        self.age += other

    @staticmethod
    def func():
        print("THIS IF FUNC")


def foo():
    def bar():
        print("in bar")

    print("in foo")
    return bar


def foobar():
    print("this is foobar")


foo()()
foobar()
