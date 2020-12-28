a = []
b = []
(c, d, e, f, g) = (1, 10, 20, 30, 7)
del a
del b, c, d, e, f, g
a = b = [10, 20, 30]
del (a, b)
