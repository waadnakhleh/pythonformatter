import sys
sys.path.append("lib")
import _rewrite


def main(*argv):
    # User must insert file name
    _rewrite.rewrite(*argv)


if __name__ == "__main__":
    main(*sys.argv)
