def handle_exception():
    pass


try:
    pass
except TypeError as e:
    handle_exception()
else:
    print("Everything as usual")
finally:
    print("some cleanup")
try:
    pass
except:
    handle_exception()
