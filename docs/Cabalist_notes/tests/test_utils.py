from utils.decompress import parse_suffix


def test_parse_suffix_end_of_line():
    info = parse_suffix("75154060000080ffffffff000100000034ffffffff")
    assert info['end_of_line'] == "75"


def test_parse_suffix_line_length_in_bytes():
    info = parse_suffix("75154060000080ffffffff000100000034ffffffff")
    assert info['line_length_in_bytes'] == "15"


def test_parse_suffix_data_bytes_in_line():
    info = parse_suffix("75154060000080ffffffff000100000034ffffffff")
    assert info['data_bytes_in_line'] == "40"


def test_parse_suffix_bit_pattern():
    info = parse_suffix("75154060000080ffffffff000100000034ffffffff")
    assert info['bit_pattern'] == "60000080"


def test_parse_suffix_remaining_line():
    info = parse_suffix("75154060000080ffffffff000100000034ffffffff")
    assert info['remaining_line'] == "ffffffff000100000034ffffffff"
