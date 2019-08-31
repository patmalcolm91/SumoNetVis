"""
Tools for plotting trajectories.

Author: Patrick Malcolm
"""

import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt


class Trajectory:
    def __init__(self, id, x=[], y=[], speed=[], angle=[], edge=[], colors=[]):
        self.x = x
        self.y = y
        self.speed = speed
        self.angle = angle
        self.edge = edge
        self.colors = colors

    def append_point(self, x=None, y=None, speed=None, angle=None, edge=None, color=None):
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

    def plot(self, ax):
        if len(self.x) < 2:
            return
        for i in range(len(self.x)-2):
            ax.plot(self.x[i:i+2], self.y[i:i+2], c=self.colors[i])
