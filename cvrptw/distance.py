from haversine import haversine, Unit
import numpy as np


def euclidean_distance(pos1, pos2):
    return int(np.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2))


def coord_distance(pos1, pos2):
    return haversine(pos1, pos2, unit=Unit.METERS)
