"""
Main classes and functions for dealing with a Sumo network.

Author: Patrick Malcolm
"""

import xml.etree.ElementTree as ET
from shapely.geometry import *
import matplotlib.patches
import matplotlib.pyplot as plt
from SumoNetVis import Utils

DEFAULT_LANE_WIDTH = 3.2
COLOR_SCHEME = {
    "junction": "#660000",
    "pedestrian": "#808080",
    "bicycle": "#C0422C",
    "ship": "#96C8C8",
    "authority": "#FF0000",
    "none": "#FFFFFF",
    "no_passenger": "#5C5C5C",
    "other": "#000000"
}
US_MARKINGS = False  # if True, US-style lane markings will be drawn


class Edge:
    def __init__(self, attrib):
        """
        Initializes an Edge object.
        :param attrib: dict of Edge attributes
        :type attrib: dict
        """
        self.id = attrib["id"]
        self.function = attrib["function"] if "function" in attrib else ""
        self.lanes = []

    def append_lane(self, lane):
        """
        Makes the specified Lane a child of the Edge
        :param lane: child Lane object
        :return: None
        :type lane: Lane
        """
        self.lanes.append(lane)
        lane.parentEdge = self

    def lane_count(self):
        """
        Returns the number of lanes to which this Edge is a parent
        :return: lane count
        """
        return len(self.lanes)

    def intersects(self, other):
        """
        Checks if any lane in the edge intersects a specified geometry
        :param other: the geometry against which to check
        :return: True if any lane intersects other, else False
        :type other: BaseGeometry
        """
        for lane in self.lanes:
            if other.intersects(lane.shape):
                return True
        return False

    def plot(self, ax):
        """
        Plots the lane
        :param ax: matplotlib Axes object
        :return: None
        :type ax: plt.Axes
        """
        for lane in self.lanes:
            lane.plot_shape(ax)
            lane.plot_lane_markings(ax)


class Lane:
    def __init__(self, attrib):
        """
        Initialize a Lane object.
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
        """
        Returns the Sumo-GUI default lane color for this lane.
        :return: lane color
        """
        if self.allow == "pedestrian":
            return COLOR_SCHEME["pedestrian"]
        if self.allow == "bicycle":
            return COLOR_SCHEME["bicycle"]
        if self.allow == "ship":
            return COLOR_SCHEME["ship"]
        if self.allow == "authority":
            return COLOR_SCHEME["authority"]
        if self.disallow == "all":
            return COLOR_SCHEME["none"]
        if "passenger" in self.disallow or "passenger" not in self.allow:
            return COLOR_SCHEME["no_passenger"]
        else:
            return COLOR_SCHEME["other"]

    def plot_alignment(self, ax):
        """
        Plots the centerline alignment of the lane
        :param ax: matplotlib Axes object
        :return: None
        :type ax: plt.Axes
        """
        x, y = zip(*self.alignment.coords)
        ax.plot(x, y)

    def plot_shape(self, ax):
        """
        Plots the entire shape of the lane
        :param ax: matplotlib Axes object
        :return: None
        :type ax: plt.Axes
        """
        poly = matplotlib.patches.Polygon(self.shape.boundary.coords, True, color=self.color)
        ax.add_patch(poly)

    def inverse_lane_index(self):
        """
        Returns the inverted lane index (i.e. counting from inside out)
        :return: inverted lane index
        """
        return self.parentEdge.lane_count() - self.index - 1

    def plot_lane_markings(self, ax):
        """
        Guesses and plots some simple lane markings. TODO: use fill_between to plot thickness in data coordinates
        :param ax: matplotlib Axes object
        :return: None
        :type ax: plt.Axes
        """
        if "passenger" in self.allow or "passenger" not in self.disallow and self.parentEdge.function != "internal":
            if self.inverse_lane_index() == 0:
                color, dashes = ("y", (1, 0)) if US_MARKINGS is True else ("w", (1, 0))
            else:
                color, dashes = "w", (3, 9)
            leftEdge = self.alignment.parallel_offset(self.width/2, side="left")
            try:
                x, y = zip(*leftEdge.coords)
                line = Utils.LineDataUnits(x, y, linewidth=0.5, color=color, dashes=dashes)
                ax.add_line(line)
            except NotImplementedError:
                print("Can't print center stripe for lane " + self.id)


class Junction:
    def __init__(self, attrib):
        """
        Initializes a Junction object.
        :param attrib: dict of junction attributes.
        :type attrib: dict
        """
        self.id = attrib["id"]
        self.shape = None
        if "shape" in attrib:
            coords = [[float(coord) for coord in xy.split(",")] for xy in attrib["shape"].split(" ")]
            if len(coords) > 2:
                self.shape = Polygon(coords)

    def plot(self, ax):
        """
        Plots the Junction.
        :param ax: matplotlib Axes object
        :return: None
        :type ax: plt.Axes
        """
        if self.shape is not None:
            poly = matplotlib.patches.Polygon(self.shape.boundary.coords, True, color=COLOR_SCHEME["junction"])
            ax.add_patch(poly)


class Net:
    def __init__(self, file):
        """
        Initializes a Net object from a Sumo network file
        :param file: path to Sumo network file
        :type file: str
        """
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

    def _get_extents(self):
        lane_geoms = []
        for edge in self.edges:
            for lane in edge.lanes:
                lane_geoms.append(lane.shape)
        polygons = MultiPolygon(lane_geoms)
        return polygons.bounds

    def plot(self, ax=None, clip_to_limits=False, zoom_to_extents=True):
        """
        Plots the Net.
        :param ax: matplotlib Axes object. Defaults to current axes.
        :param clip_to_limits: if True, only objects in the current view will be drawn. Speeds up saving of animations.
        :param zoom_to_extents: if True, window will be set to the network extents. Ignored if clip_to_limits is True
        :return: None
        :type ax: plt.Axes
        :type clip_to_limits: bool
        :type zoom_to_extents: bool
        """
        if ax is None:
            ax = plt.gca()
        if zoom_to_extents and not clip_to_limits:
            x_min, y_min, x_max, y_max = self._get_extents()
            ax.set_xlim(x_min, x_max)
            ax.set_ylim(y_min, y_max)
        ax.set_clip_box(ax.get_window_extent())
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        bounds = [[xmin, ymax], [xmax, ymax], [xmax, ymin], [xmin, ymin]]
        window = Polygon(bounds)
        for edge in self.edges:
            if not clip_to_limits or edge.intersects(window):
                edge.plot(ax)
        for junction in self.junctions:
            if not clip_to_limits or (junction.shape is not None and junction.shape.intersects(window)):
                junction.plot(ax)


if __name__ == "__main__":
    net = Net('../MT_Course.net.xml')
    fig, ax = plt.subplots()
    net.plot(ax)
    plt.show()
