class MyDecorator:
    pass
@MyDecorator
class AnotherOne():
    pass

class YetAnotherClass(AnotherOne, metaclass=MyDecorator):
    pass

a = YetAnotherClass()
class MyClass(AnotherOne, MyDecorator, metaclass=YetAnotherClass, private=True):
    pass
b = MyClass()

