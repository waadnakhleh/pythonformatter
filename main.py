import sys
sys.path.append("lib")
import _rewrite


def main(*argv):
    _rewrite.rewrite(*argv)


if __name__ == "__main__":
    main(*sys.argv)
