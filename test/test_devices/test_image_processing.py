import time
from pathlib import Path

import cv2
import numpy as np

from ot2util.devices.image_processing import get_colors, match_size

TEST_DIR = Path(__file__).parent


def test_get_colors():
    img = cv2.imread(str(TEST_DIR / "IMG_1812.png"))
    img = match_size(img, (1280, 1920))
    s = time.time()
    colors = get_colors(img)  # noqa
    e = time.time()
    print(e - s)
    print(colors[1]["A1"])
    assert np.array_equal(colors[1]["A1"], [161, 163, 215])
    # from pprint import pprint
    # pprint(colors)
    # print(colors[1]['A2'])
    return
