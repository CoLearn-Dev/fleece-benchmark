OUTPUT_PIC = "data/pic"
OUTPUT_RESULT = "data/result"

from collections import namedtuple

ALL_PATH = namedtuple("ALL_PATH", ["OUTPUT_PIC", "OUTPUT_RESULT"])(
    OUTPUT_PIC, OUTPUT_RESULT
)


def init_all_path():
    import os

    for path in ALL_PATH:
        if not os.path.exists(path):
            os.makedirs(path)


if __name__ == "__main__":
    init_all_path()
    print("init all finish: ", ALL_PATH)
