import pytest

from tests.line_data import AN_8PX_BLACK_LINE_AN_8PX_WHITE_LINE_AN_8PX_BLACK_LINE_MOVING_LEFT_TO_RIGHT_8PX_AT_A_TIME
from tests.line_data import AN_8PX_LINE_MOVING_LEFT_TO_RIGHT_8PX_AT_A_TIME
from tests.line_data import AN_8PX_LINE_MOVING_LEFT_TO_RIGHT_8PX_AT_A_TIME_OFFSET_BY_1
from tests.utils import simplify_binary_line
from utils.decompress import recreate_line


@pytest.mark.parametrize("test_input,expected", AN_8PX_LINE_MOVING_LEFT_TO_RIGHT_8PX_AT_A_TIME)
def test_8px_lines_are_correct_length(test_input, expected):
    assert len(recreate_line(test_input)) == 512


@pytest.mark.parametrize("test_input,expected", AN_8PX_LINE_MOVING_LEFT_TO_RIGHT_8PX_AT_A_TIME)
def test_8px_lines_are_correct_value(test_input, expected):
    assert simplify_binary_line(recreate_line(test_input)) == expected


@pytest.mark.parametrize("test_input,expected", AN_8PX_LINE_MOVING_LEFT_TO_RIGHT_8PX_AT_A_TIME_OFFSET_BY_1)
def test_8px_lines_are_correct_length(test_input, expected):
    assert len(recreate_line(test_input)) == 512


@pytest.mark.parametrize("test_input,expected", AN_8PX_LINE_MOVING_LEFT_TO_RIGHT_8PX_AT_A_TIME_OFFSET_BY_1)
def test_8px_lines_are_correct_value(test_input, expected):
    assert simplify_binary_line(recreate_line(test_input)) == expected


@pytest.mark.parametrize("test_input,expected", AN_8PX_BLACK_LINE_AN_8PX_WHITE_LINE_AN_8PX_BLACK_LINE_MOVING_LEFT_TO_RIGHT_8PX_AT_A_TIME)
def test_8px_dashed_lines_are_correct_length(test_input, expected):
    assert len(recreate_line(test_input)) == 512


@pytest.mark.parametrize("test_input,expected", AN_8PX_BLACK_LINE_AN_8PX_WHITE_LINE_AN_8PX_BLACK_LINE_MOVING_LEFT_TO_RIGHT_8PX_AT_A_TIME)
def test_8px_dashed_lines_are_correct_value(test_input, expected):
    assert simplify_binary_line(recreate_line(test_input)) == expected


def test_17px_dashed_lines_are_correct_length():
    line = "7520400000048000007fffc0001ffff00007fffc0001ffff0070032a0007ffff"
    assert len(recreate_line(line)) == 512


def test_17px_dashed_lines_are_correct_value():
    line = "7520400000048000007fffc0001ffff00007fffc0001ffff0070032a0007ffff"
    assert simplify_binary_line(recreate_line(line)) == [17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 17, 2]

# def test_25px_checkerboard_first_line_correct_length():
#     line = "752d40000000880000007fffffc000001ffffff0000007fffffc000001ffffff0000700321fffff00000008000"
#     assert len(recreate_line(line)) == 512
#
# def test_25px_checkerboard_first_line_correct_value():
#     line = "752d40000000880000007fffffc000001ffffff0000007fffffc000001ffffff0000700321fffff00000008000"
#     assert simplify_binary_line(recreate_line(line)) == [25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 25, 12]
#
