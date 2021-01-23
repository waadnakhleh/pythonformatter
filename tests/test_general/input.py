import random
class Ages():
    def __init__(self, age=None):
        if not age:
            age = random.choice(range(0,99))
        self.age = age

    def __str__(self):
        return  str(self.age)
    def __add__(self , other):
        self.age +=        other
    @staticmethod
    def func():
        print("THIS IF FUNC")



def foo():
    def bar():
        print(           "in bar")
    print("in foo")
    return bar
def foobar():
    print ("this is foobar")
foo()()
foobar()
a =Ages(2)
b = Ages()