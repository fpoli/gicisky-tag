from pathlib import Path

from PIL import Image

CHUNK_SIZE = 36


def get_chunks(a_str, chunk_size):
    return [a_str[i:i + chunk_size] for i in range(0, len(a_str), chunk_size)]


def get_binary_chunks(a_str, chunk_size):
    for each_byte in get_chunks(a_str, chunk_size):
        # print(f"{int(each_byte, 16):08b}")
        yield int(each_byte, 16)


def create_image_from_binary(data, width, height):

    im = Image.new('L', (width, height), "black")

    cmap = {'0': 0,
            '1': 255,
            'e': 100}

    data = [cmap[bit] for bit in data]

    im.putdata(data)
    return im


def create_ascii_image_from_binary(data, width, height):
    cmap = {'0': "░",
            '1': "█",
            'e': "X"}

    with open("ascii_image_format.txt", "w") as output:
        for each_chunk in get_chunks(data, width):
            for c in each_chunk:
                output.write(cmap[c])
            output.write("\n")


if __name__ == "__main__":

    successful_img_captures = Path("successful_img_captures")
    for each_file in successful_img_captures.iterdir():
        if not each_file.suffix == ".txt":
            continue
        output_dir = successful_img_captures / each_file.stem
        output_dir.mkdir(exist_ok=True)

        with open(each_file) as f, \
                open(output_dir / "formatted_image_data.hex", "w") as hex_output, \
                open(output_dir / "big_endian_formatted_image_data.hex", "w") as big_endian_hex_output, \
                open(output_dir / "formatted_image_data.bin", "wb") as bin_output:

            image_data = ""
            first_line = True
            for each_line in f:
                # Line number is first 8 bytes (64bit)
                # 2a000000 -> 0000 002a (42)
                line_number = each_line[:8]
                # output.write(line_number + "\n")
                if first_line:
                    # On the first line is the image size.  In this case:
                    # 983a0000 -> 0000 3a98 (15000)
                    image_size = each_line[8:16]
                    # output.write(image_size + "\n")
                    first_line = False
                    remaining_line = each_line[16:]
                else:
                    remaining_line = each_line[8:]

                image_data += remaining_line.strip()
            # 75 seems to be the line delimiter
            all_data = []
            longest_dataline = -1
            for dataline in image_data.split("75"):
                if dataline:

                    dataline = "75" + dataline

                    hex_formatted_dataline = "".join(get_chunks(dataline, 2))
                    big_endian_hex_formatted_dataline = "".join(reversed(get_chunks(dataline, 2)))

                    bin_dataline = list(get_binary_chunks(hex_formatted_dataline, 2))
                    big_endian_bin_dataline = list(get_binary_chunks(big_endian_hex_formatted_dataline, 2))

                    bin_formatted_dataline = "".join(f"{c:08b}" for c in bin_dataline)
                    big_endian_bin_formatted_dataline = "".join(f"{c:08b}" for c in big_endian_bin_dataline)
                    if len(bin_formatted_dataline) > longest_dataline:
                        longest_dataline = len(bin_formatted_dataline)

                    # # Add whitespace around some things
                    # line_start = hex_formatted_dataline[:2]
                    #
                    # # Line Length in hex (in half) (i.e. 8 bit word count)
                    # line_length_in_hex = hex_formatted_dataline[2:4]
                    #
                    # # Data bytes in line.  Usually 512bits
                    # data_length = hex_formatted_dataline[4:6]
                    #
                    # known_first_chunk_values = {
                    #     "1000": 4,
                    #     "2000": 5,
                    #     "4000": 6,
                    #     "8000": 7,
                    #     "0001": 8,
                    #     "0002": 9,
                    #     "0004": 10,
                    #     "0008": 11,
                    #     "1001": 12,
                    #     "1002": 13,
                    # }
                    #
                    # # Information about data chunks.  Still somewhat unknown
                    # chunk_1_prefix = hex_formatted_dataline[6:10]
                    # chunk_2_prefix = hex_formatted_dataline[10:14]
                    #
                    # remaining_dataline = hex_formatted_dataline[14:]
                    #
                    # if chunk_1_prefix in known_first_chunk_values:
                    #     chunk1_length = known_first_chunk_values[chunk_1_prefix] * 2
                    #     midpoint = remaining_dataline[chunk1_length:chunk1_length + 6]
                    #     if not (midpoint.startswith("0000") or midpoint.startswith("ffff")):
                    #         print("Uh...")
                    #         print(midpoint)
                    #         midpoint = ""
                    #         chunk1_data = ""
                    #     else:
                    #         chunk1_data = remaining_dataline[:chunk1_length]
                    #         remaining_dataline = remaining_dataline[chunk1_length + 6:]
                    #
                    #
                    #
                    #
                    #
                    # hex_formatted_dataline = " ".join([line_start, line_length_in_hex, data_length, chunk_1_prefix, chunk_2_prefix, chunk1_data, midpoint, remaining_dataline])

                    all_data.append(big_endian_bin_formatted_dataline)
                    hex_output.write(f"{hex_formatted_dataline}\n")
                    big_endian_hex_output.write(f"{big_endian_hex_formatted_dataline}\n")
                    bin_output.write(bytes(bin_dataline))

            all_data = ["e" * (longest_dataline - len(dl)) + dl for dl in all_data]
            bitmap = create_image_from_binary("".join(all_data), longest_dataline, len(all_data))
            bitmap.save(output_dir / "bitmap.bmp")

            # create_ascii_image_from_binary("".join(all_data), longest_dataline, len(all_data))
