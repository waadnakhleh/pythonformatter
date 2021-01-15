(x, y) = (10, 20)
def foo():
    global x, y
    x = 20
    y = 10


print(x, y)
foo()
print(x, y)
