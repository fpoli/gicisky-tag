from itertools import groupby
from typing import Tuple


def simplify_binary_line(binstring: str) -> Tuple[int]:
    if set(binstring) - {'0', '1'}:
        raise ValueError(f"Line contains non binary characters! {set(binstring) - {0, 1} }")
    split_string = [''.join(group) for key, group in groupby(binstring)]
    if split_string and "1" not in split_string[0]:
        count = [0]
    else:
        count = []
    count += [len(s) for s in split_string]
    return tuple(count)
