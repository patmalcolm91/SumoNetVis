"""
Tools for plotting trajectories.

Author: Patrick Malcolm
"""

import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np


class Trajectory:
    def __init__(self, id, time=[], x=[], y=[], speed=[], angle=[], edge=[], colors=[]):
        self.id = id
        self.time = time
        self.x = x
        self.y = y
        self.speed = speed
        self.angle = angle
        self.edge = edge
        self.colors = colors

    def append_point(self, time, x, y, speed=None, angle=None, edge=None, color=None):
        self.time.append(time)
        self.x.append(x)
        self.y.append(y)
        self.speed.append(speed)
        self.angle.append(angle)
        self.edge.append(edge)
        self.colors.append(color)

    def assign_colors_constant(self, color):
        self.colors = [color for i in self.x]

    def assign_colors_speed(self, cmap, min_speed, max_speed):
        raise NotImplementedError("Function not yet implemented")

    def assign_colors_angle(self, cmap):
        raise NotImplementedError("Function not yet implemented")

    def assign_colors_edge(self, cmap):
        raise NotImplementedError("Function not yet implemented")

    def plot(self, ax, start_time=0, end_time=np.inf):
        if len(self.x) < 2:
            return
        for i in range(len(self.x)-2):
            if self.time[i] < start_time:
                continue
            if self.time[i+1] > end_time:
                break
            ax.plot(self.x[i:i+2], self.y[i:i+2], c=self.colors[i])
