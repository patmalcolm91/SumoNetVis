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


class _POI:
    def __init__(self, attrib):
        """
        Initializes a Sumo additionals POI.

        :param attrib: a dict of all the POI's XML attributes
        :type attrib: dict
        """
        self.id = attrib["id"]
        self.color = _Utils.convert_sumo_color(attrib["color"])
        self.x, self.y = None, None
        if "x" in attrib and "y" in attrib:
            self.x = float(attrib["x"])
            self.y = float(attrib["y"])
        elif "lane" in attrib and "lanePos" in attrib:
            warnings.warn("POI locations defined relative to lanes not supported.")
        elif "lat" in attrib and "lon" in attrib:
            warnings.warn("POI locations defined as lat/lon not supported.")
        else:
            raise ValueError("POI " + self.id + " has no valid position attributes.")
        self.type = attrib.get("type", "")
        self.layer = float(attrib.get("layer", "0"))
        self.imgFile = attrib.get("imgFile", None)
        if self.imgFile is not None:
            warnings.warn("Display of POIs in additional files as images not supported.")
        self.width = float(attrib.get("width", 0))
        self.height = float(attrib.get("height", 0))
        self.angle = float(attrib.get("angle", 0))

    def plot(self, ax, **kwargs):
        """
        Plot the POI.

        :param ax: matplotlib Axes object
        :param kwargs: kwargs to pass to the plotting function
        :return: None
        :type ax: plt.Axes
        """
        kwargs = {"radius": 1, "zorder": self.layer-110 if self.layer <= 0 else self.layer-90, **kwargs}
        if self.x is not None and self.y is not None:
            circle = matplotlib.patches.Circle((self.x, self.y), color=self.color, **kwargs)
            ax.add_patch(circle)


class Additionals:
    def __init__(self, file):
        """
        Reads objects from a Sumo additional XML file.

        :param file: path to Sumo additional file
        """
        self.polys = dict()
        self.pois = dict()
        root = ET.parse(file).getroot()
        for obj in root:
            if obj.tag == "poly":
                poly = _Poly(obj.attrib)
                self.polys[poly.id] = poly
            elif obj.tag == "poi":
                poi = _POI(obj.attrib)
                self.pois[poi.id] = poi

    def plot_polygons(self, ax=None, **kwargs):
        """
        Plot all polygons.

        :param ax: matplotlib Axes object
        :param kwargs: kwargs to pass to the plotting function
        :return: None
        :type ax: plt.Axes
        """
        if ax is None:
            ax = plt.gca()
        for poly in self.polys.values():
            poly.plot(ax, **kwargs)

    def plot_pois(self, ax=None, **kwargs):
        """
        Plot all POIs.

        :param ax: matplotlib Axes object
        :param kwargs: kwargs to pass to the plotting function
        :return: None
        :type ax: plt.Axes
        """
        if ax is None:
            ax = plt.gca()
        for poi in self.pois.values():
            poi.plot(ax, **kwargs)

    def plot(self, ax=None, polygon_kwargs=None, poi_kwargs=None, **kwargs):
        """
        Plot all supported objects contained within the Additionals object.
        Kwargs are passed to the plotting functions, with object-specific kwargs overriding general ones.

        :param ax: matplotlib Axes object
        :param polygon_kwargs: kwargs to pass to the polygon plotting function
        :param poi_kwargs: kwargs to pass to the POI plotting function
        :return: None
        :type ax: plt.Axes
        :type polygon_kwargs: dict
        :type poi_kwargs: dict
        """
        if ax is None:
            ax = plt.gca()
        if polygon_kwargs is None:
            polygon_kwargs = dict()
        if poi_kwargs is None:
            poi_kwargs = dict()
        for poly in self.polys.values():
            poly.plot(ax, **{**kwargs, **polygon_kwargs})
        for poi in self.pois.values():
            poi.plot(ax, **{**kwargs, **poi_kwargs})


if __name__ == "__main__":
    addls = Additionals("../Sample/test.add.xml")
    addls.plot()
    plt.gca().set_aspect("equal")
    plt.show()
