"""
Tools for dealing with Lane- and Edge-based traffic measure output files.
"""

import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np
import warnings

MEASURE_TYPES = {
    "sampled_seconds": float,
    "traveltime": float,
    "density": float,
    "occupancy": float,
    "waitingTime": float,
    "speed": float,
    "departed": int,
    "arrived": int,
    "entered": int,
    "left": int,
    "laneChangedFrom": int,
    "laneChangedTo": int
}


class _NetworkBasedMeasures:
    def __init__(self, files=None):
        self.data = dict()  # dict like {interval: data} where data is a dict like {edge_id: attributes_dict}
        if type(files) == str:
            self.load_file(files)
        elif files is not None:
            for file in files:
                self.load_file(file)

    def load_file(self, file):
        raise NotImplementedError("Method load_file() must be overridden by child class.")

    @property
    def intervals(self):
        return sorted(self.data.keys())

    def __getitem__(self, item):
        if type(item) == tuple and len(item) == 2 and item in self.data:
            return self.data[item]
        for interval, interval_data in self.data.items():
            if interval[0] <= item < interval[1]:
                return interval_data
        raise IndexError("Time", item, "not contained in any interval.")

    def __iter__(self):
        return iter(sorted(self.data.keys()))


class EdgeBasedMeasures(_NetworkBasedMeasures):
    def load_file(self, file):
        root = ET.parse(file).getroot()
        for interval in root:
            if interval.tag != "interval":
                continue
            interval_tuple = (float(interval.attrib["begin"]), float(interval.attrib["end"]))
            if interval_tuple not in self.data:
                self.data[interval_tuple] = dict()
            for edge in interval:
                if edge.tag != "edge":
                    continue
                for attr in edge.attrib:
                    if attr in MEASURE_TYPES:
                        edge.attrib[attr] = MEASURE_TYPES[attr](edge.attrib[attr])
                if edge.attrib["id"] not in self.data[interval_tuple]:
                    self.data[interval_tuple][edge.attrib["id"]] = dict()
                self.data[interval_tuple].update({edge.attrib["id"]: edge.attrib})


class LaneBasedMeasures(_NetworkBasedMeasures):
    def load_file(self, file):
        root = ET.parse(file).getroot()
        for interval in root:
            if interval.tag != "interval":
                continue
            interval_tuple = (float(interval.attrib["begin"]), float(interval.attrib["end"]))
            if interval_tuple not in self.data:
                self.data[interval_tuple] = dict()
            for edge in interval:
                if edge.tag != "edge":
                    continue
                for lane in edge:
                    if lane.tag != "lane":
                        continue
                    for attr in edge.attrib:
                        if attr in MEASURE_TYPES:
                            lane.attrib[attr] = MEASURE_TYPES[attr](lane.attrib[attr])
                    if lane.attrib["id"] not in self.data[interval_tuple]:
                        self.data[interval_tuple][lane.attrib["id"]] = dict()
                    self.data[interval_tuple].update({lane.attrib["id"]: lane.attrib})


class MeanDataPlot:
    _DEFAULT_CMAPS_AND_RANGES = {
        "speed": ("viridis", (0, 41.67)),  # viridis colormap with speed range 0-150 kph
        "occupancy": ("jet", (0, 100)),  # jet colormap with occupancy range 0-100 percent
        "density": ("jet", (0, 200))  # jet colormap with density range 0-200 veh/km
    }

    _DEFAULT_LINEWIDTH_MAPS = {
        "speed": lambda s: np.interp(s, (0, 41.67), (0, 8)),  # speed range 0-150 kph, lw range 0-8 px
        "occupancy": lambda occ: np.interp(occ, (0, 100), (0, 8)),  # occupancy range 0-100 percent, lw range 0-8 px
        "density": lambda k: np.interp(k, (0, 200), (0, 8)),  # density range 0-200 veh/km, lw range 0-8 px
    }

    def __init__(self, net, measures, color_by=None, linewidth_by=None, color_map=None, linewidth_map=None,
                 color_by_range=None, linewidth_by_range=None, lane_mode=False, **kwargs):
        """
        Class for generating a plot using Edge- or Lane-based traffic measures. Supports animation blitting.

        Coloring works as follows: color = color_map(value), where value = measures[time][sumo_id][attribute].
        color_map and color_by_range will be assigned defaults for some common color_by values.
        color_map can be specified either as a callable (in which case color_by_range is ignored), or the name of
        a matplotlib cmap, in which case value will be mapped from the range color_by_range to (0, 1) and then passed
        to the corresponding cmap.

        :param net: SumoNetVis Net object to use for plot
        :type net: SumoNetVis.Net.Net
        :param measures: object containing edge- or lane-based measures. Must be indexable like so: measures[time][sumo_id][attribute]
        :type measures: _NetworkBasedMeasures
        :param color_by: attribute in measures by which to assign color. If None, color will not be animated.
        :type color_by: str
        :param linewidth_by: attribute in measures by which to assign linewidth. If None, linewidth will not be animated.
        :param color_map: callable color map of signature: color_map(attribute_value) -> color
        :param linewidth_map: callable linewidth map of signature: linewidth_map(attribute_value) -> linewidth
        :param color_by_range: range from which to scale color values, or the max value of the range.
        :param linewidth_by_range: range from which to scale linewidth values, or the max value of the range.
        :param lane_mode: If True, lanes will be plotted instead of edges.
        :type lane_mode: bool
        :param kwargs: all kwargs will be passed to the plotting function net.plot_schematic()
        """
        self.net = net
        self.measures = measures
        # Interpret the color_map parameter and use default settings for some typical use cases
        if type(color_by_range) in [int, float]:
            color_by_range = (0, color_by_range)
        if color_by is not None and color_map is None and color_by_range is None:
            _cmap, _crange = self._DEFAULT_CMAPS_AND_RANGES.get(color_by, ("jet", (0, 1)))
            _crange = color_by_range if color_by_range is not None else _crange
            color_map = lambda x: plt.get_cmap(_cmap)(np.interp(x, _crange, (0, 1)))
        else:
            _crange = color_by_range if color_by_range is not None else (0, 1)
            if type(color_map) == str:
                _cmap = plt.get_cmap(color_map)
                color_map = lambda x: plt.get_cmap(_cmap)(np.interp(x, _crange, (0, 1)))
            elif color_map is None:
                color_map = lambda x: plt.get_cmap("jet")(np.interp(x, _crange, (0, 1)))
            elif not callable(color_map):
                raise TypeError("Invalid color_map specification.")
            elif color_by_range is not None:
                warnings.warn("Parameter color_by_range will be ignored, as a callable color_map was provided.")
        # Interpret the linewidth_map parameter
        if type(linewidth_by_range) in [int, float]:
            linewidth_by_range = (0, linewidth_by_range)
        if linewidth_map is None:
            linewidth_map = self._DEFAULT_LINEWIDTH_MAPS.get(linewidth_by, lambda x: np.interp(x, linewidth_by_range, (0, 1)))
        elif not callable(color_map):
            raise TypeError("Invalid linewidth_map specification.")
        # initialize remaining class members
        self.color_by = color_by
        self.linewidth_by = linewidth_by
        self.color_map = color_map
        self.linewidth_map = linewidth_map
        self.lane_mode = lane_mode
        self.kwargs = kwargs
        self._artists = []

    def plot(self, time, ax=None):
        """
        Plot (or update the plot of) the network, with properties based on the measures at the specified time.

        :param time: time (or interval) for which to plot
        :param ax: matplotlib Axes object
        :type ax: plt.Axes
        :return: list of matplotlib Artist objects
        """
        if ax is None:
            ax = plt.gca()
        data = self.measures[time]
        if len(self._artists) == 0:
            ac = self.net.plot_schematic(ax, **self.kwargs)
            if self.lane_mode:
                self._artists = ac.lanes
            else:
                self._artists = ac.edges
        for artist in self._artists:
            sumo_id = artist.sumo_object.id
            if sumo_id not in data:
                continue
            if self.color_by is not None:
                color = self.color_map(data[sumo_id][self.color_by])
                artist.set_color(color)
            if self.linewidth_by is not None:
                lw = self.linewidth_map(data[sumo_id][self.linewidth_by])
                artist.set_linewidth(lw)
        return self._artists


if __name__ == "__main__":
    import SumoNetVis.Net as Net
    from matplotlib.animation import FuncAnimation
    net = Net("../Sample/test.net.xml")
    edgeMeasures = EdgeBasedMeasures("../Sample/edgeBasedTest.xml")
    mdp = MeanDataPlot(net, edgeMeasures, color_by="occupancy", color_map=plt.get_cmap("Reds"), linewidth=4)
    a = FuncAnimation(plt.gcf(), mdp.plot, mdp.measures.intervals, blit=True, repeat=True)
    plt.show()
