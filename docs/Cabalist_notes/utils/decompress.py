from typing import Dict, List, Tuple

from utils.common import get_chunks, swap_endianness

compression_marker_lookup_table = {
    "0f00": "000011",
    "0e00": "000010",
    "0d00": "00000F",
    "0c00": "00000E",
    "0b00": "00000D",
    "0a00": "00000C",
    "0900": "00000B",
    "0800": "00000A",
    "0700": "000009",
    "0600": "000008",
    "0500": "000007",
    "0400": "000006",
    "0300": "000005",
    "0200": "000004",
    "0100": "000003",
}


def parse_suffix(data_line: str) -> Dict[str, str]:
    remaining_line = data_line
    end_of_line = remaining_line[:2]
    remaining_line = remaining_line[2:]
    line_length_in_bytes = remaining_line[:2]
    remaining_line = remaining_line[2:]
    data_bytes_in_line = remaining_line[:2]
    remaining_line = remaining_line[2:]
    bit_pattern = remaining_line[:8]
    remaining_line = remaining_line[8:]
    return {
        "end_of_line": end_of_line,
        "line_length_in_bytes": line_length_in_bytes,
        "data_bytes_in_line": data_bytes_in_line,
        "bit_pattern": bit_pattern,
        "remaining_line": remaining_line
    }


def decode_compression_marker(compression_marker) -> int:
    if len(compression_marker) == 4:
        multiplier = compression_marker_lookup_table.get(compression_marker)
    else:
        multiplier = compression_marker

    if multiplier is None:
        raise ValueError(f"Unknown compression marker: {compression_marker}")
    return int(multiplier, 16)


def get_binary_of_compression_pattern(byte) -> str:
    """
    This seems too complicated for what it does.
    There is probably a binary operator I'm not aware of.
    """
    reverse_byte = swap_endianness(byte)
    return f"{int(reverse_byte, 16):032b}"[::-1]


def split_label_line_data(dataline: str, bin_compression_pattern: str) -> List[Tuple[str, str]]:
    split_line = []
    current_data = ""
    remaining_line = dataline

    for bit in bin_compression_pattern:
        if not remaining_line:
            continue

        if bit == "0":
            current_data += remaining_line[:2]
            remaining_line = remaining_line[2:]
        elif bit == "1":
            if current_data:
                split_line.append(("data", current_data))
            current_data = ""
            compression_marker = remaining_line[:4]
            if compression_marker == "0000":
                compression_marker = remaining_line[:6]
                remaining_line = remaining_line[6:]
            else:
                remaining_line = remaining_line[4:]

            split_line.append(("compression", compression_marker))

        else:
            raise ValueError("Invalid bit in compression pattern")

    else:
        if remaining_line:
            current_data += remaining_line

        if current_data:
            split_line.append(("data", current_data))

    return split_line


def expand_compression_markers(a_split_line):

    uncompressed_line = ""
    last_byte = "00"
    first_marker = True
    next_byte_multiplier = 0
    for i, (label, each_chunk) in enumerate(a_split_line):
        if label == "data":
            uncompressed_line += next_byte_multiplier * f"{int(each_chunk[:2], 16):08b}"
            next_byte_multiplier = 0
            for each_byte in get_chunks(each_chunk, 2):
                uncompressed_line += f"{int(each_byte, 16):08b}"
                last_byte = each_byte
        elif label == "compression":
            try:
                multiplier = decode_compression_marker(each_chunk)
            except ValueError as e:
                print(e)
                multiplier = 0

            # The compression mark logic would seem to work like this:
            # The first one must pull from the LEFT.
            #    UNLESS it next to another one then it pulls from the RIGHT.
            # All other compression markers pull from the RIGHT

            if first_marker and a_split_line[i + 1][0] != "compression":
                uncompressed_line += multiplier * f"{int(last_byte, 16):08b}"
            else:
                next_byte_multiplier += multiplier
            first_marker = False
    return uncompressed_line


def recreate_line(data_line: str) -> str:
    suffix = parse_suffix(data_line)
    remaining_line = suffix["remaining_line"]
    bin_compression_pattern = get_binary_of_compression_pattern(suffix['bit_pattern'])
    split_line = split_label_line_data(remaining_line, bin_compression_pattern)
    return expand_compression_markers(split_line)
