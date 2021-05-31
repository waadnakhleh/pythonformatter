def foo(a, b="Test", *, c="AnotherTest"):
    pass

class Bar(metaclass=foo):
    pass

foo(a="1",b="2",c="3")