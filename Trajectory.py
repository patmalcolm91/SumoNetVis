"""
Tools for plotting trajectories.

Author: Patrick Malcolm
"""

import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
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

    def assign_colors_speed(self, cmap, min_speed, max_speed):
        raise NotImplementedError("Function not yet implemented")

    def assign_colors_angle(self, cmap):
        raise NotImplementedError("Function not yet implemented")

    def assign_colors_edge(self, cmap):
        raise NotImplementedError("Function not yet implemented")

    def plot(self, ax, start_time=0, end_time=np.inf):
        """
        Plots the trajectory
        :param ax: matplotlib Axes object
        :param start_time: time at which to start drawing
        :param end_time: time at which to end drawing
        :type ax: plt.Axes
        :type start_time: float
        :type end_time: float
        :return: None
        """
        if len(self.x) < 2:
            return
        for i in range(len(self.x)-2):
            if self.time[i] < start_time:
                continue
            if self.time[i+1] > end_time:
                break
            ax.plot(self.x[i:i+2], self.y[i:i+2], c=self.colors[i])


class Trajectories:
    def __init__(self, file=None):
        """
        Initializes a Trajectories object.
        :param file: file from which to read trajectories
        :type file: str
        """
        self.trajectories = []  # type: list[Trajectory]
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
            for veh in timestep:
                time = float(timestep.attrib["time"])
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

    def plot(self, ax, start_time=0, end_time=np.inf):
        """
        Plots all of the trajectories contained in this object.
        :param ax: matplotlib Axes object
        :param start_time: time at which to start drawing
        :param end_time: time at which to stop drawing
        :return: None
        :type ax: plt.Axes
        :type start_time: float
        :type end_time: float
        """
        for trajectory in self:
            trajectory.plot(ax, start_time, end_time)


if __name__ == "__main__":
    trajectories = Trajectories("../2019-08-30-17-01-38fcd-output.xml")
    fig, ax = plt.subplots()
    trajectories["TESIS_0"].plot(ax)
    plt.show()
