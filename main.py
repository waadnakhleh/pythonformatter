import sys
import traceback

sys.path.append("lib")
import _rewrite


def main(*argv):
    try:
        _rewrite.rewrite(*argv)
    except:
        traceback.print_exc()
        exit(2)


if __name__ == "__main__":
    main(*sys.argv)
