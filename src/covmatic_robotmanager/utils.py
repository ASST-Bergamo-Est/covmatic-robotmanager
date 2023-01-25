import math


def rad2deg(rad_list):
    return [r * 360 / (2 * math.pi) for r in rad_list]
