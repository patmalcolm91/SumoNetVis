"""
Main classes and functions for dealing with a Sumo network.

Author: Patrick Malcolm
"""

import xml.etree.ElementTree as ET
from shapely.geometry import *
import matplotlib.patches
import matplotlib.pyplot as plt

DEFAULT_LANE_WIDTH = 3.2
US_MARKINGS = False  # if True, US-style lane markings will be drawn


class Edge:
    def __init__(self, attrib):
        self.id = attrib["id"]
        self.function = attrib["function"] if "function" in attrib else ""
        self.lanes = []

    def append_lane(self, lane):
        self.lanes.append(lane)
        lane.parentEdge = self

    def lane_count(self):
        return len(self.lanes)

    def plot(self, ax):
        for lane in self.lanes:
            lane.plot_shape(ax)
            lane.plot_lane_markings(ax)


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
        self.color = self.lane_color()
        self.parentEdge = None

    def lane_color(self):
        if self.allow == "pedestrian":
            return "#808080"
        if self.allow == "bicycle":
            return "#C0422C"
        if self.allow == "ship":
            return "#96C8C8"
        if self.allow == "authority":
            return "#FF0000"
        if self.disallow == "all":
            return "#FFFFFF"
        if "passenger" in self.disallow or "passenger" not in self.allow:
            return "#5C5C5C"
        else:
            return "#000000"

    def plot_alignment(self, ax):
        x, y = zip(*self.alignment.coords)
        ax.plot(x, y)

    def plot_shape(self, ax):
        poly = matplotlib.patches.Polygon(self.shape.boundary.coords, True, color=self.color)
        ax.add_patch(poly)

    def inverse_lane_index(self):
        return self.parentEdge.lane_count() - self.index - 1

    def plot_lane_markings(self, ax):
        """
        Guesses and plots some simple lane markings. TODO: use fill_between to plot thickness in data coordinates
        :param ax:
        :return:
        """
        if "passenger" in self.allow or "passenger" not in self.disallow and self.parentEdge.function != "internal":
            if self.inverse_lane_index() == 0:
                fmt = "y-" if US_MARKINGS is True else "w-"
            else:
                fmt = "w--"
            leftEdge = self.alignment.parallel_offset(self.width/2, side="left")
            try:
                x, y = zip(*leftEdge.coords)
                ax.plot(x, y, fmt)
            except NotImplementedError:
                print("Can't print center stripe for lane " + self.id)


class Junction:
    def __init__(self, attrib):
        self.id = attrib["id"]
        self.shape = None
        if "shape" in attrib:
            coords = [[float(coord) for coord in xy.split(",")] for xy in attrib["shape"].split(" ")]
            if len(coords) > 2:
                self.shape = Polygon(coords)

    def plot(self, ax):
        if self.shape is not None:
            poly = matplotlib.patches.Polygon(self.shape.boundary.coords, True, color="#660000")
            ax.add_patch(poly)


class Net:
    def __init__(self, file):
        self.edges = []
        self.junctions = []
        net = ET.parse(file).getroot()
        for obj in net:
            if obj.tag == "edge":
                edge = Edge(obj.attrib)
                for laneObj in obj:
                    lane = Lane(laneObj.attrib)
                    edge.append_lane(lane)
                self.edges.append(edge)
            elif obj.tag == "junction":
                junction = Junction(obj.attrib)
                self.junctions.append(junction)

    def plot(self, ax):
        for edge in self.edges:
            edge.plot(ax)
        for junction in self.junctions:
            junction.plot(ax)


if __name__ == "__main__":
    net = Net('../MT_Course.net.xml')
    fig, ax = plt.subplots()
    net.plot(ax)
    plt.show()
