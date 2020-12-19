for i in range(1000):
    pass
names = ["George", "Sohail", "Waad"]
for name in names:
    print(name)
    if name not in ["George", "Sohail", "Waad"]:
        print("There is an impostor among us")
        break
else:
    print("finished regularly")
for (i, name) in enumerate(names):
    print(i, " ", name)
def new_func():
    b = 0
    for i in range(50):
        while b != 10:
            print(b)
            b = b + 1
        assert b == 10


new_func()
