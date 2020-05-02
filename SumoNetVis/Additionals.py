"""
Main classes and functions for dealing with Sumo "additional" files.
"""

import warnings
import xml.etree.ElementTree as ET
from shapely.geometry import *
import matplotlib.patches
import matplotlib.pyplot as plt
from SumoNetVis import _Utils


class _Poly:
    def __init__(self, attrib):
        """
        Initializes a Sumo additionals polygon.

        :param attrib: a dict of all the poly's XML attributes
        :type attrib: dict
        """
        self.id = attrib["id"]
        coords = [[float(coord) for coord in xy.split(",")] for xy in attrib["shape"].split(" ")]
        self.fill = attrib.get("fill", "f") in ["t", "true", "1"]
        self.shape = Polygon(coords) if self.fill else LineString(coords)
        self.color = _Utils.convert_sumo_color(attrib["color"])
        self.geo = attrib.get("geo", "f") in ["t", "true", "1"]
        if self.geo:
            warnings.warn("Geographic coordinates not supported for polygons in additional files.")
        self.lineWidth = float(attrib.get("lineWidth", 1))
        self.layer = float(attrib.get("layer", "0"))
        self.type = attrib.get("type", "")
        self.imgFile = attrib.get("imgFile", None)
        if self.imgFile is not None:
            warnings.warn("Display of polygons in additional files as images not supported.")
        self.angle = float(attrib.get("angle", 0))

    def plot(self, ax, **kwargs):
        """
        Plot the polygon.

        :param ax: matplotlib Axes object
        :param kwargs: kwargs to pass to the plotting function
        :return: None
        :type ax: plt.Axes
        """
        kwargs = {"zorder": self.layer-110 if self.layer <= 0 else self.layer-90, **kwargs}
        if self.fill is True:
            if "lw" not in kwargs and "linewidth" not in kwargs:
                kwargs["lw"] = 0
            poly = matplotlib.patches.Polygon(self.shape.boundary.coords, True, color=self.color, **kwargs)
            ax.add_patch(poly)
        else:
            x, y = zip(*self.shape.coords)
            line = _Utils.LineDataUnits(x, y, linewidth=self.lineWidth, color=self.color, **kwargs)
            ax.add_line(line)


class Additionals:
    def __init__(self, file):
        """
        Reads objects from a Sumo additional XML file.

        :param file: path to Sumo additional file
        """
        self.polys = dict()
        root = ET.parse(file).getroot()
        for obj in root:
            if obj.tag == "poly":
                poly = _Poly(obj.attrib)
                self.polys[poly.id] = poly

    def plot_polygons(self, ax=None, **kwargs):
        if ax is None:
            ax = plt.gca()
        for poly in self.polys.values():
            poly.plot(ax, **kwargs)


if __name__ == "__main__":
    addls = Additionals("../Sample/test.add.xml")
    addls.plot_polygons()
    plt.gca().set_aspect("equal")
    plt.show()
