from itertools import groupby, zip_longest
from typing import Iterator, List, Tuple

from utils.common import get_chunks
from utils.decompress import decode_compression_marker, get_binary_of_compression_pattern, parse_suffix, recreate_line, split_label_line_data

VERTICAL_BAR = "┊"

INSTRUCTION_ARROW = "I"
DATA_ARROW = "D"


def replace_all_chrs(a_list: List[str], a_chr: str) -> Iterator[str]:
    for each_word in a_list:
        yield a_chr * len(each_word)


def _annotate_suffix(bit_pattern: str, data_bytes_in_line: str, line_length_in_bytes: str, end_of_line: str, annotation_stack_height: int) -> List[str]:
    suffix = [end_of_line, line_length_in_bytes, data_bytes_in_line, bit_pattern]
    lines = []
    lines.append(" ".join(suffix) + " ")
    lines.append(" ".join(replace_all_chrs(suffix, INSTRUCTION_ARROW)) + " ")
    for i in range(annotation_stack_height - 1):
        lines.append(" ".join(replace_all_chrs(suffix, VERTICAL_BAR)) + " ")
    lines.append(" ".join(replace_all_chrs(suffix[:-1], VERTICAL_BAR)) + "  Bit pattern for compression markers")
    lines.append(" ".join(replace_all_chrs(suffix[:-1], VERTICAL_BAR)) + "    └ " + " ".join(get_chunks(get_binary_of_compression_pattern(bit_pattern), 4)))
    lines.append(" ".join(replace_all_chrs(suffix[:-1], VERTICAL_BAR)) + "    └     * Applied in reverse")
    lines.append(" ".join(replace_all_chrs(suffix[:-1], VERTICAL_BAR)))
    lines.append(" ".join(replace_all_chrs(suffix[:-2], VERTICAL_BAR)) + f"  Line represents this many bytes ({int(data_bytes_in_line, 16)}B) ({int(data_bytes_in_line, 16) * 8}b)")
    lines.append(" ".join(replace_all_chrs(suffix[:-3], VERTICAL_BAR)) + f"  Line Length in bytes ({int(line_length_in_bytes, 16)}B) (36 characters)")

    lines.append("End of Line")

    return lines


def _space_data(data_chunk: str) -> str:
    line = ""
    for each_byte in get_chunks(data_chunk, 2):
        line += f" {int(each_byte, 16):08b}"
    return line


def _annotate_compression_marker(labeled_line: List[Tuple[str, str]], compression_chunk_idx: int, first_marker: bool) -> Tuple[str, List[str]]:
    warnings = []
    compression_marker = labeled_line[compression_chunk_idx][1]

    if first_marker and labeled_line[compression_chunk_idx + 1][0] != "compression":
        polarity = "Left"
    else:
        polarity = "Right"

    if polarity == "Left":
        if labeled_line[compression_chunk_idx - 1][0] == "compression":
            offset = -2
        else:
            offset = -1
        byte_to_decompress = labeled_line[compression_chunk_idx + offset][1][-2:].upper()
    else:
        try:
            if labeled_line[compression_chunk_idx + 1][0] == "compression":
                offset = 2
            else:
                offset = 1
        except IndexError:
            msg = "- WARNING:  Issue with the Compression Marker's index.  Reached end of line before reaching compression marker"
            warnings.append(msg)
            print(msg)
            offset = 0
        byte_to_decompress = labeled_line[compression_chunk_idx + offset][1][:2].upper()
    try:
        multiplier = decode_compression_marker(compression_marker)
    except ValueError as e:
        msg = f"- Unknown compression marker: {compression_marker}"
        warnings.append(msg)
        multiplier = 0

    annotation = f" There are {multiplier} bytes (0x{multiplier:X}) of 0x{byte_to_decompress} ({'<-' if polarity == 'Left' else '->'} {polarity} single byte pattern {'<-' if polarity == 'Left' else '->'})"
    return annotation, warnings


def _annotate_data(labeled_line: List[Tuple[str, str]]) -> Tuple[List[str], List[str]]:
    arrow_line = []
    value_line = []
    lines = []

    warnings = []

    # First we create the arrows and the lines pointing to those arrows
    _just_values = [v[1] for v in labeled_line]
    lines.append(" ".join(replace_all_chrs(_just_values, VERTICAL_BAR)) + " ")
    for i, (label, value) in enumerate(labeled_line):
        if i:
            lines.append(" ".join(replace_all_chrs(_just_values[:-1 * i], VERTICAL_BAR)) + " ")
        value_line.append(value)
        if label == "data":
            arrow_line.append(DATA_ARROW * len(value))
        elif label == "compression":
            arrow_line.append(INSTRUCTION_ARROW * len(value))
        else:
            raise ValueError(f"Unknown data label: {label}")

    lines.append("")  # Final Label line

    # Now we create the actual labels
    first_marker = True
    for i, (label, value) in enumerate(labeled_line):
        if label == "data":
            lines[len(lines) - 1 - i] += _space_data(value)

        elif label == "compression":
            compression_annotation, compression_warnings = _annotate_compression_marker(labeled_line, i, first_marker)
            warnings += compression_warnings
            lines[len(lines) - 1 - i] += compression_annotation
            first_marker = False

        else:
            raise ValueError(f"Unknown data label: {label}")

    annotation = [" ".join(value_line), " ".join(arrow_line), *lines]

    return annotation, warnings


def annotate(dataline: str) -> str:
    """
    Return a large multi line annotated version of this dataline
    """

    warnings = []

    suffix = parse_suffix(dataline)
    split_line = split_label_line_data(suffix["remaining_line"], get_binary_of_compression_pattern(suffix['bit_pattern']))
    data_annotations, data_warnings = _annotate_data(split_line)
    warnings += data_warnings
    suffix_annotations = _annotate_suffix(bit_pattern=suffix['bit_pattern'],
                                          data_bytes_in_line=suffix['data_bytes_in_line'],
                                          line_length_in_bytes=suffix['line_length_in_bytes'],
                                          end_of_line=suffix['end_of_line'],
                                          annotation_stack_height=len(data_annotations))

    annotations = zip_longest(suffix_annotations, data_annotations, fillvalue="")

    result = ["".join(each) for each in annotations]
    result.append("")
    result += warnings
    result.append("")
    uncompressed_line = recreate_line(dataline)
    if len(uncompressed_line) != 512:
        len_diff = 512 - len(uncompressed_line)
        warnings.append(f"- WARNING: Line length is too {'short' if len_diff > 0 else 'long'}.  Expected: 512   Actual: {len(uncompressed_line)}  Difference: {len(uncompressed_line) - 512}")

    groups = groupby(uncompressed_line)
    runs = [(label, sum(1 for _ in group)) for label, group in groups]
    run_line_labels = ""
    run_line_labels_hex = ""
    run_line = ""
    for _, count in runs:
        if count == 1:
            run_line += "│"
            run_line_labels += "1"
            run_line_labels_hex += "1"
        else:
            run_line += "╭"
            for _ in range(count - 2):
                run_line += "─"
            run_line += "╮"
            run_line_labels += f"{count:^{count}}"
            if count > 3:
                count_as_padded_hex = f"0x{count:02X}"
            else:
                count_as_padded_hex = str(count)
            run_line_labels_hex += f"{count_as_padded_hex:^{count}}"

    result.append(run_line_labels_hex)
    result.append(run_line_labels)
    result.append(run_line)

    result.append(uncompressed_line.replace("0", "█").replace("1", " "))
    result.append("".join(get_chunks(uncompressed_line, 8)))
    result.append(("┕" + "━" * 6 + "┙") * 64)

    byte_count = []
    for i in range(64):
        i = f"{i:02}"
        byte_count.append(f"{i:^8}")

    result.append("".join(byte_count))

    hex_data_values = []
    bin_chunks = get_chunks(uncompressed_line, 8)
    for each in bin_chunks:
        hex_rep = f"(0x{int(each[:4], 2):X}{int(each[4:], 2):X})"
        hex_data_values.append(f"{hex_rep:^8}")

    result.append("".join(hex_data_values))

    return "\n".join(result)
