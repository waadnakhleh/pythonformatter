import sys
import _rewrite


def main(*argv):
    _rewrite.rewrite(*argv)


if __name__ == "__main__":
    main(*sys.argv)
