"""
Tools for plotting trajectories.

Author: Patrick Malcolm
"""

import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np


class Trajectory:
    def __init__(self, id, time=None, x=None, y=None, speed=None, angle=None, lane=None, colors=None):
        self.id = id
        self.time = time if time is not None else []
        self.x = x if x is not None else []
        self.y = y if y is not None else []
        self.speed = speed if speed is not None else []
        self.angle = angle if angle is not None else []
        self.lane = lane if lane is not None else []
        self.colors = colors if colors is not None else []

    def append_point(self, time, x, y, speed=None, angle=None, lane=None, color="#000000"):
        """
        Appends a point to the trajectory
        :type time: float
        :type x: float
        :type y: float
        :type speed: float
        :type angle: float
        :type lane: str
        :type color: str
        :return: None
        """
        self.time.append(time)
        self.x.append(x)
        self.y.append(y)
        self.speed.append(speed)
        self.angle.append(angle)
        self.lane.append(lane)
        self.colors.append(color)

    def assign_colors_constant(self, color):
        """
        Assigns a constant color to the trajectory
        :param color: desired color
        :return: None
        """
        self.colors = [color for i in self.x]

    def assign_colors_speed(self, cmap=None, min_speed=0, max_speed=None):
        """
        Assigns colors to trajectory points based on the speed.
        :param cmap: cmap object or name of cmap to use
        :param min_speed: speed corresponding to low end of the color scale. If None, trajectory's min value is used
        :param max_speed: speed corresponding to high end of the color scale. If None, trajectory's max value is used
        :return:None
        :type min_speed: float
        :type max_speed: float
        """
        if cmap is None:
            cmap = plt.cm.get_cmap("viridis")
        elif type(cmap) == str:
            cmap = plt.cm.get_cmap(cmap)
        cmapList = cmap.colors
        if min_speed is None:
            min_speed = min(self.speed)
        if max_speed is None:
            max_speed = max(self.speed)
        for i in range(len(self.x)):
            index = len(cmapList) * (self.speed[i] - min_speed) / (max_speed - min_speed)
            index = int(round(max(0, min(index, len(cmapList)-1))))
            color = cmapList[index]
            self.colors[i] = color

    def assign_colors_angle(self, cmap=None, angle_mode="deg"):
        """
        Assigns colors to trajectory points based on the angle.
        :param cmap: cmap object or name of cmap to use
        :param angle_mode: units of the angle value. "deg", "rad", or "grad"
        :type angle_mode: str
        :return: None
        """
        if cmap is None:
            cmap = plt.cm.get_cmap("hsv")
        elif type(cmap) == str:
            cmap = plt.cm.get_cmap(cmap)
        max_angles = {"deg": 360, "rad": 2*np.pi, "grad": 400}
        max_angle = max_angles[angle_mode]
        for i in range(len(self.x)):
            angle = self.angle[i] % max_angle
            color = cmap(angle/max_angle)
            self.colors[i] = color

    def assign_colors_lane(self, cmap=None, color_dict=None):
        """
        Assigns colors to the trajectory points based on the lane value
        :param cmap: cmap object or name of cmap to use to color lanes
        :param color_dict: dict to override random color selection. Keys are lane IDs, values are colors.
        :return: None
        :type color_dict: dict
        """
        if cmap is None:
            cmap = plt.cm.get_cmap("tab10")
        elif type(cmap) == str:
            cmap = plt.cm.get_cmap(cmap)
        cmapList = cmap.colors
        if color_dict is None:
            color_dict = dict()
            lane_list = set(self.lane)
            for i, lane in enumerate(lane_list):
                color_dict[lane] = cmapList[i % len(cmapList)]
        for i in range(len(self.x)):
            self.colors[i] = color_dict[self.lane[i]]

    def plot(self, ax=None, start_time=0, end_time=np.inf, zoom_to_extents=False, **kwargs):
        """
        Plots the trajectory
        :param ax: matplotlib Axes object. Defaults to current axes.
        :param start_time: time at which to start drawing
        :param end_time: time at which to end drawing
        :param zoom_to_extents: if True, window will be set to Trajectory extents
        :param kwargs: keyword arguments to pass to LineCollection or matplotlib.pyplot.plot()
        :type ax: plt.Axes
        :type start_time: float
        :type end_time: float
        :type zoom_to_extents: bool
        :return: None
        """
        if ax is None:
            ax = plt.gca()
        if len(self.x) < 2:
            return
        segs, colors = [], []  # line segments and colors
        x_min, y_min, x_max, y_max = np.inf, np.inf, -np.inf, -np.inf
        for i in range(len(self.x)-2):
            if self.time[i] < start_time:
                continue
            if self.time[i+1] > end_time:
                break
            if zoom_to_extents:
                x_min, x_max = min(x_min, self.x[i]), max(x_max, self.x[i])
                y_min, y_max = min(y_min, self.y[i]), max(y_max, self.y[i])
            segs.append([[self.x[i], self.y[i]], [self.x[i+1], self.y[i+1]]])
            colors.append(self.colors[i])
        lc = LineCollection(segs, colors=colors, **kwargs)
        ax.add_collection(lc)
        if zoom_to_extents:
            dx, dy = x_max - x_min, y_max - y_min
            ax.set_xlim([x_min-0.05*dx, x_max+0.05*dx])
            ax.set_ylim([y_min-0.05*dy, y_max+0.05*dy])


class Trajectories:
    def __init__(self, file=None):
        """
        Initializes a Trajectories object.
        :param file: file from which to read trajectories
        :type file: str
        """
        self.trajectories = []  # type: list[Trajectory]
        self.start = None
        self.end = None
        self.timestep = None
        if file is not None:
            if file.endswith("fcd-output.xml"):
                self.read_from_fcd(file)
            else:
                raise NotImplementedError("Reading from this type of file not implemented: " + file)

    def __iter__(self):
        return iter(self.trajectories)

    def __next__(self):
        return next(self.trajectories)

    def __getitem__(self, i):
        if type(i) == str:
            for trajectory in self.trajectories:
                if trajectory.id == i:
                    return trajectory
            raise IndexError
        elif type(i) == int:
            return self.items[i]
        else:
            raise TypeError("Index type " + type(i).__name__ + " not supported by class " + type(self).__name__)

    def append(self, trajectory):
        self.trajectories.append(trajectory)

    def read_from_fcd(self, file):
        """
        Reads trajectories from Sumo floating car data (fcd) output file.
        :param file: Sumo fcd output file
        :return: None
        :type file: str
        """
        root = ET.parse(file).getroot()
        trajectories = dict()
        for timestep in root:
            time = float(timestep.attrib["time"])
            if self.timestep is None and self.start is not None:
                self.timestep = time - self.start
            if self.start is None:
                self.start = time
            self.end = time
            for veh in timestep:
                if veh.tag == "vehicle":
                    vehID = veh.attrib["id"]
                    if vehID not in trajectories:
                        trajectories[vehID] = Trajectory(vehID)
                    x = float(veh.attrib["x"])
                    y = float(veh.attrib["y"])
                    lane = veh.attrib["lane"]
                    speed = float(veh.attrib["speed"])
                    angle = float(veh.attrib["angle"])
                    trajectories[vehID].append_point(time, x, y, speed, angle, lane)
        for vehID in trajectories:
            self.append(trajectories[vehID])

    def plot(self, ax=None, start_time=0, end_time=np.inf, **kwargs):
        """
        Plots all of the trajectories contained in this object.
        :param ax: matplotlib Axes object. Defaults to current axes.
        :param start_time: time at which to start drawing
        :param end_time: time at which to stop drawing
        :param kwargs: keyword arguments to pass to plot function
        :return: None
        :type ax: plt.Axes
        :type start_time: float
        :type end_time: float
        """
        if ax is None:
            ax = plt.gca()
        for trajectory in self:
            trajectory.plot(ax, start_time, end_time, **kwargs)


if __name__ == "__main__":
    trajectories = Trajectories("../2019-08-30-17-01-38fcd-output.xml")
    fig, ax = plt.subplots()
    trajectories["TESIS_0"].assign_colors_angle()
    trajectories["TESIS_0"].plot(ax, lw=3)
    plt.show()
