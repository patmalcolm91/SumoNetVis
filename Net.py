"""
Main classes and functions for dealing with a Sumo network.

Author: Patrick Malcolm
"""

import xml.etree.ElementTree as ET
from shapely.geometry import *
import matplotlib.patches
import matplotlib.pyplot as plt

DEFAULT_LANE_WIDTH = 3.2


class Lane:
    def __init__(self, attrib):
        """
        Initialize a lane object
        :param attrib: dict of all of the lane attributes
        :type attrib: dict
        """
        self.id = attrib["id"]
        self.index = int(attrib["index"])
        self.speed = float(attrib["speed"])
        self.allow = attrib["allow"] if "allow" in attrib else ""
        self.disallow = attrib["disallow"] if "disallow" in attrib else ""
        self.width = float(attrib["width"]) if "width" in attrib else DEFAULT_LANE_WIDTH
        self.endOffset = attrib["endOffset"] if "endOffset" in attrib else 0
        self.acceleration = attrib["acceleration"] if "acceleration" in attrib else "False"
        coords = [[float(coord) for coord in xy.split(",")] for xy in attrib["shape"].split(" ")]
        self.alignment = LineString(coords)
        self.shape = self.alignment.buffer(self.width/2, cap_style=CAP_STYLE.flat)

    def plot_alignment(self, ax):
        x, y = zip(*self.alignment.coords)
        ax.plot(x, y)

    def plot_shape(self, ax):
        poly = matplotlib.patches.Polygon(self.shape.boundary.coords, True, color="green")
        ax.add_patch(poly)


if __name__ == "__main__":
    netFile = ET.parse('../MT_Course.net.xml')
    net = netFile.getroot()
    fig, ax = plt.subplots()
    for obj in net:
        if obj.tag == "edge":
            for lane in obj:
                ln = Lane(lane.attrib)
                ln.plot_alignment(ax)
                ln.plot_shape(ax)
    plt.show()
