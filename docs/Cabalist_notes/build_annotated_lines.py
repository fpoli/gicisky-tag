# This targets Github for markdown and color formatting in markdown.

from pathlib import Path

from utils.annotate import annotate
from utils.common import DATA_LINE_START_COORDS

SKIPLIST = [  # These are blank lines that don't need to be included hundreds/thousands of times in our annotations:
    "751240100000800000000000003800000000",
    "75124010000080ffffffff000038ffffffff",
    "75111810000080000000000e0000000000",
    "75111810000080ffffffff0e00ffffffff",

]


def convert_image_data_to_datalines(image_data):
    datalines = []
    while image_data:
        if image_data[:2] != "75":
            raise ValueError("Corrupt image data.  Line did not start with delimiter")

        line_length = int(image_data[2:4], 16) * 2  # Hex number each character is half a byte
        datalines.append(image_data[:line_length])
        image_data = image_data[line_length:]
    return datalines


if __name__ == "__main__":
    successful_img_captures = Path('successful_img_captures')

    for dump_path in successful_img_captures.iterdir():
        with open(dump_path) as dump_data:
            if ".DS_Store" in dump_path.stem:
                continue
            image_data = ""
            first_line = True
            for each_line in dump_data:
                # Line number is first 8 bytes (64bits)
                # 2a000000 -> 0000 002a (42)
                line_number = each_line[:8]
                remaining_line = each_line[8:]
                if first_line:
                    # On the first line is the image size.  In this case:
                    # 983a0000 -> 0000 3a98 (15000)
                    image_size = remaining_line[:8]
                    # output.write(image_size + "\n")
                    first_line = False
                    remaining_line = remaining_line[8:]

                image_data += remaining_line.strip()  # Remove all the newlines
            all_data = []
            longest_dataline = -1
        datalines = convert_image_data_to_datalines(image_data)
        skip_count = 0
        with open(Path('annotations', dump_path.stem + ".md"), 'w') as output:
            for i, each_dataline in enumerate(datalines):
                if each_dataline in SKIPLIST:
                    skip_count += 1
                    continue
                # TODO fill in the blanks below
                output.write(f"\nDataline #: {i} Starting at coordinates: {DATA_LINE_START_COORDS[i]}\n")
                output.write("```diff\n")
                output.write(annotate(each_dataline))
                output.write('\n```\n')
            if skip_count:
                output.write(f"\nSkipped {skip_count} lines that were all black or all white.\n")


# TODO This doesn't gracefully handle 192px lines