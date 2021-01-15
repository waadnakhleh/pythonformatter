import random


try:
    if random.choice(range(1, 100)):
        raise random.choice([TypeError, RuntimeError])
    else:
        pass


except RuntimeError:
    pass
try:

    raise TypeError("Hello")
except TypeError as exc:
    raise RuntimeError from exc




