from pathlib import PosixPath


class NonePath(PosixPath):

    def __bool__(self):
        return False

NONE_PATH = NonePath("/dev/null/void")
