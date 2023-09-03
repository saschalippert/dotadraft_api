import logging

import cv2

logger = logging.getLogger()
logger.setLevel(logging.INFO)

target_resolution_map = {}

target_resolution_map["4_3"] = (1920, 1440)
target_resolution_map["16_9"] = (1920, 1080)
target_resolution_map["16_10"] = (1680, 1050)
target_resolution_map["21_9"] = (2560, 1080)

aspect_ratio_map = {}

aspect_ratio_map["1920_1440"] = "4_3"
aspect_ratio_map["1600_1200"] = "4_3"
aspect_ratio_map["1280_960"] = "4_3"
aspect_ratio_map["1152_864"] = "4_3"
aspect_ratio_map["1024_768"] = "4_3"
aspect_ratio_map["800_600"] = "4_3"
aspect_ratio_map["640_480"] = "4_3"
aspect_ratio_map["2560_1440"] = "16_9"
aspect_ratio_map["1920_1080"] = "16_9"
aspect_ratio_map["1600_900"] = "16_9"
aspect_ratio_map["1366_768"] = "16_9"
aspect_ratio_map["1280_720"] = "16_9"
aspect_ratio_map["1920_1200"] = "16_10"
aspect_ratio_map["1680_1050"] = "16_10"
aspect_ratio_map["1440_900"] = "16_10"
aspect_ratio_map["1280_800"] = "16_10"
aspect_ratio_map["3440_1440"] = "21_9"
aspect_ratio_map["2560_1080"] = "21_9"
aspect_ratio_map["1280_1024"] = "4_3"
aspect_ratio_map["1440_960"] = "16_10"
aspect_ratio_map["720_480"] = "16_10"


def get_indices(start, count):
    return [a for a in range(start, start + count)]


def idx_player(i):
    if i == 0:
        return get_indices(6, 4)
    elif i == 1:
        return get_indices(26, 4)
    elif i == 2:
        return get_indices(46, 4)
    elif i == 3:
        return get_indices(66, 4)
    elif i == 4:
        return get_indices(80, 4)
    elif i == 5:
        return get_indices(10, 4)
    elif i == 6:
        return get_indices(36, 4)
    elif i == 7:
        return get_indices(50, 4)
    elif i == 8:
        return get_indices(70, 4)
    elif i == 9:
        return get_indices(84, 4)

    raise Exception("idx out of bounds")


def idx_radiant():
    idx = []

    idx.extend(idx_player(0))
    idx.extend(idx_player(1))
    idx.extend(idx_player(2))
    idx.extend(idx_player(3))
    idx.extend(idx_player(4))

    return idx


def idx_dire():
    idx = []

    idx.extend(idx_player(5))
    idx.extend(idx_player(6))
    idx.extend(idx_player(7))
    idx.extend(idx_player(8))
    idx.extend(idx_player(9))

    return idx


def idx_main():
    idx = []

    idx.extend(get_indices(0, 6))
    idx.extend(get_indices(14, 6))
    idx.extend(get_indices(20, 6))
    idx.extend(get_indices(30, 6))
    idx.extend(get_indices(40, 6))
    idx.extend(get_indices(54, 6))
    idx.extend(get_indices(60, 6))
    idx.extend(get_indices(74, 6))

    return idx


def crop(screen, points):
    pos_x = points[:, 0]
    pos_y = points[:, 1]

    return screen[min(pos_y): max(pos_y), min(pos_x): max(pos_x)]


def resize_screen(screen):
    height, width, channels = screen.shape

    resolution = f"{width}_{height}"

    if resolution in aspect_ratio_map:
        aspect_ratio = aspect_ratio_map[resolution]

        if aspect_ratio in target_resolution_map:
            logger.info(f"aspect ratio found {resolution} {aspect_ratio}")
            target_resolution = target_resolution_map[aspect_ratio]
            screen = cv2.resize(screen, target_resolution, interpolation=cv2.INTER_AREA)
            return screen, aspect_ratio

    raise Exception(f"resolution {resolution} not found")
