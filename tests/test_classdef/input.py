class MyDecorator:
    pass
@MyDecorator
class AnotherOne():
    pass

class YetAnotherClass(AnotherOne, metaclass=MyDecorator):
    pass

a = YetAnotherClass()
