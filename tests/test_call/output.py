print("Hello, world!")
func_call(7, 2, name, *arg, d=True, c=False, **kwrags)
a = "My_string"
if hasattr("str", "__len__"):
    print("a has attribute called __len__ ")
else:
    print("a doesn't have __len__ attribute")


def bar(first_argument, this_is_the_second_argument, this_is_the_third_argument):
    pass


bar(
    "Here is the first argument",
    this_is_the_second_argument="This is the second argument",
    this_is_the_third_argument="enough"
)
