import os
from typing import List


def listenv(envname: str, default: List[str]) -> List[str]:
    if envname in os.environ:
        return os.getenv(envname).split(",")
    return default