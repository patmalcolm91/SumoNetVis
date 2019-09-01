"""
Tools for plotting trajectories.

Author: Patrick Malcolm
"""

import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np


class Trajectory:
    def __init__(self, id, time=None, x=None, y=None, speed=None, angle=None, edge=None, colors=None):
        self.id = id
        self.time = time if time is not None else []
        self.x = x if x is not None else []
        self.y = y if y is not None else []
        self.speed = speed if speed is not None else []
        self.angle = angle if angle is not None else []
        self.edge = edge if edge is not None else []
        self.colors = colors if colors is not None else []

    def append_point(self, time, x, y, speed=None, angle=None, edge=None, color=None):
        """
        Appends a point to the trajectory
        :type time: float
        :type x: float
        :type y: float
        :type speed: float
        :type angle: float
        :type edge: str
        :type color: str
        :return: None
        """
        self.time.append(time)
        self.x.append(x)
        self.y.append(y)
        self.speed.append(speed)
        self.angle.append(angle)
        self.edge.append(edge)
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
