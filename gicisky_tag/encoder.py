import math
from enum import Enum
from PIL import Image
import numpy as np
from os import path
from gicisky_tag.log import logger

black_color = [0, 0, 0] # [47, 36, 41]
white_color = [255, 255, 255] # [242, 244, 239]
red_color = [255, 0, 0] # [215, 38, 39]
gray_color = [128, 128, 128]
blue_color = [0, 0, 255]
ciano_color = [0, 255, 255]
green_color = [0, 255, 0]
yellow_color = [255, 255, 0]
magenta_color = [255, 0, 255]


def quantize_image_simple_colors(image, debug_folder=None):
    """Quantize the image to simple colors.
    """
    quant_palette_image = Image.new("P", (1,1))
    quant_palette_image.putpalette(
        black_color + white_color
        + red_color + blue_color + green_color
        + yellow_color + magenta_color + ciano_color
        + gray_color
    )
    quant_image = image.convert("RGB").quantize(
        palette=quant_palette_image,
        dither=Image.FLOYDSTEINBERG,
    )

    if debug_folder is not None:
        quant_image.save(path.join(debug_folder, "simple_image.png"))

    return quant_image


class Dither(Enum):
    """Dithering method.

    Possible values:
    * NONE: no dithering, just choose the closest color for each pixel.
    * FLOYDSTEINBERG: quantize the image using Floyd-Steinberg dithering.
    * COMBINED: quantize grayscale and red colors independently using Floyd-Steinberg dithering,
        then combine them. This usually limits the usage of red to the areas where it is really
        needed.
    """
    NONE = "none"
    FLOYDSTEINBERG = "floydsteinberg"
    COMBINED = "combined"

    def __str__(self):
        return self.value


def dither_image_bwr(image, dithering, debug_folder=None):
    """Dither the image using black, white and red.
    """
    if dithering not in Dither:
        raise ValueError(f"Invalid dithering parameter: {dither}")

    if dithering in (Dither.NONE, Dither.FLOYDSTEINBERG):
        bwr_palette_image = Image.new("P", (1,1))
        bwr_palette_image.putpalette(black_color + white_color + red_color)
        quant_image = image.convert("RGB").quantize(
            palette=bwr_palette_image,
            dither=Image.NONE if dithering == Dither.NONE else Image.FLOYDSTEINBERG,
        )

        if debug_folder is not None:
            quant_image.save(path.join(debug_folder, "quant_image.png"))

        return quant_image

    elif dithering == Dither.COMBINED:
        quant_image = quantize_image_simple_colors(image, debug_folder=debug_folder).convert("RGB")

        bw_image = image.convert("1")
        bw_bitmap = np.asarray(bw_image).astype(bool)
        assert bw_bitmap.shape == image.size[::-1], f"Expected shape {image.size[::-1]}, but got {bw_bitmap.shape}"

        red_bitmap = (np.asarray(quant_image) == red_color).all(axis=-1)
        assert red_bitmap.shape == image.size[::-1], f"Expected shape {image.size[::-1]}, but got {red_bitmap.shape}"

        bwr_pixels = np.zeros((*image.size[::-1], 3), dtype=np.uint8)
        bwr_pixels[red_bitmap] = red_color
        bwr_pixels[(red_bitmap == False) & bw_bitmap] = white_color
        bwr_pixels[(red_bitmap == False) & (bw_bitmap == False)] = black_color
        bwr_image = Image.fromarray(bwr_pixels, "RGB")

        if debug_folder is not None:
            bw_image.save(path.join(debug_folder, "bw_image.png"))
            Image.fromarray(np.uint8(bw_bitmap * 255), "L").save(
                path.join(debug_folder, "bw_bitmap.png")
            )
            Image.fromarray(np.uint8(red_bitmap * 255), "L").save(
                path.join(debug_folder, "red_bitmap.png")
            )
            bwr_image.save(
                path.join(debug_folder, "bwr_image.png")
            )

        return bwr_image


def encode_image(image, dithering=Dither.NONE, debug_folder=None):
    bwr_image = dither_image_bwr(image, dithering=dithering, debug_folder=debug_folder)
    bwr_pixels = np.asarray(bwr_image.convert("RGB")).astype(int)

    bw_bitmap = (bwr_pixels == white_color).all(axis=-1)
    bw_bitmap = np.flipud(np.rot90(bw_bitmap))
    assert bw_bitmap.shape == image.size, f"Expected shape {image.size}, but got {bw_bitmap.shape}"

    red_bitmap = (bwr_pixels == red_color).all(axis=-1)
    red_bitmap = np.flipud(np.rot90(red_bitmap))
    assert red_bitmap.shape == image.size, f"Expected shape {image.size}, but got {red_bitmap.shape}"

    bw_data = compress_bitmap(np.packbits(bw_bitmap, axis=-1), image.size)
    red_data = compress_bitmap(np.packbits(red_bitmap, axis=-1), image.size)

    image_data = bytearray(bw_data) + bytearray(red_data)
    image_data = len(image_data).to_bytes(4, "little") + image_data
    return image_data


def compress_bitmap(bitmap, image_shape):
    expected_shape = (250, 122)
    # TODO: make sure that the compression works well for other image sizes
    assert image_shape == expected_shape, f"Expected image of shape {expected_shape}, but got {image_shape}"

    width, height = image_shape
    encoded_bitmap = []
    assert 0 < width
    assert 0 < height <= 128
    assert len(bitmap) == width
    num_line_bytes = math.ceil(height / 8) # 1 byte = 8 pixels
    compression_markers = [0b00000000, 0b00000000, 0b00000000, 0b00000000]
    for col in range(width):
        line_bitvec = list(bitmap[col])
        assert len(line_bitvec) == num_line_bytes, f"Line {col} has {len(line_bitvec)} elements, but should have {num_line_bytes} elements."
        encoded_line = [0x75, 3 + len(compression_markers) + len(line_bitvec), num_line_bytes] + compression_markers + line_bitvec
        encoded_bitmap += encoded_line
    return encoded_bitmap
