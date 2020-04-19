"""
Main classes and functions for dealing with a Sumo network.
"""

import xml.etree.ElementTree as ET
from shapely.geometry import *
import shapely.ops as ops
import matplotlib.patches
import matplotlib.pyplot as plt
import numpy as np
from SumoNetVis import _Utils

DEFAULT_LANE_WIDTH = 3.2
STRIPE_WIDTH_SCALE_FACTOR = 1  # factor by which to scale striping widths
COLOR_SCHEME = {
    "junction": "#660000",
    "pedestrian": "#808080",
    "bicycle": "#C0422C",
    "ship": "#96C8C8",
    "authority": "#FF0000",
    "none": "#FFFFFF",
    "no_passenger": "#5C5C5C",
    "crosswalk": "#00000000",
    "other": "#000000"
}
USA_STYLE = "USA"
EUR_STYLE = "EUR"
LANE_MARKINGS_STYLE = EUR_STYLE  # desired lane marking style


def set_style(style="EUR"):
    """
    Sets the lane marking style to either USA or EUR.

    :param style: desired style ("USA" or "EUR")
    :return: None
    :type style: str
    """
    global LANE_MARKINGS_STYLE
    if style not in [USA_STYLE, EUR_STYLE]:
        raise IndexError("Specified lane marking style not supported: " + style)
    LANE_MARKINGS_STYLE = style


def set_stripe_width_scale(factor=1):
    """
    Sets the lane striping width scale factor.

    :param factor: desired scale factor
    :return: None
    :type factor: float
    """
    global STRIPE_WIDTH_SCALE_FACTOR
    STRIPE_WIDTH_SCALE_FACTOR = factor


class _Edge:
    def __init__(self, attrib):
        """
        Initializes an Edge object.

        :param attrib: dict of Edge attributes
        :type attrib: dict
        """
        self.id = attrib["id"]
        self.function = attrib["function"] if "function" in attrib else "normal"
        self.from_junction_id = attrib["from"] if "from" in attrib else None
        self.to_junction_id = attrib["to"] if "to" in attrib else None
        self.from_junction = None
        self.to_junction = None
        self.lanes = []
        self.stop_offsets = []

    def append_lane(self, lane):
        """
        Makes the specified Lane a child of the Edge

        :param lane: child Lane object
        :return: None
        :type lane: _Lane
        """
        self.lanes.append(lane)
        lane.parentEdge = self

    def get_lane(self, index):
        """
        Returns the lane on the Edge with the given index

        :param index: lane index of Lane to retrieve
        :return: Lane
        """
        for lane in self.lanes:
            if lane.index == index:
                return lane
        raise IndexError("Edge contains no Lane with given index.")

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

    def append_stop_offset(self, attrib):
        value = float(attrib["value"])
        vc = attrib["vClasses"] if "vClasses" in attrib else ""
        exceptions = attrib["exceptions"] if "exceptions" in attrib else ""
        vClasses = _Utils.Allowance(allow_string=vc, disallow_string=exceptions)
        self.stop_offsets.append((value, vClasses))

    def plot(self, ax, lane_kwargs=None, lane_marking_kwargs=None, **kwargs):
        """
        Plots the lane.
        The lane_kwargs and lane_markings_kwargs override the general kwargs for their respective functions.

        :param ax: matplotlib Axes object
        :param lane_kwargs: kwargs to pass to the lane plotting function (matplotlib.patches.Polygon())
        :param lane_marking_kwargs: kwargs to pass to the lane markings plotting function (matplotlib.lines.Line2D())
        :return: None
        :type ax: plt.Axes
        """
        if lane_kwargs is None:
            lane_kwargs = dict()
        if lane_marking_kwargs is None:
            lane_marking_kwargs = dict()
        for lane in self.lanes:
            lane.plot_shape(ax, **{**kwargs, **lane_kwargs})
            lane.plot_lane_markings(ax, **{**kwargs, **lane_marking_kwargs})


class _Lane:
    def __init__(self, attrib):
        """
        Initialize a Lane object.

        :param attrib: dict of all of the lane attributes
        :type attrib: dict
        """
        self.id = attrib["id"]
        self.index = int(attrib["index"])
        self.speed = float(attrib["speed"])
        allow_string = attrib["allow"] if "allow" in attrib else ""
        disallow_string = attrib["disallow"] if "disallow" in attrib else ""
        self.allows = _Utils.Allowance(allow_string, disallow_string)
        self.width = float(attrib["width"]) if "width" in attrib else DEFAULT_LANE_WIDTH
        self.endOffset = attrib["endOffset"] if "endOffset" in attrib else 0
        self.acceleration = attrib["acceleration"] if "acceleration" in attrib else "False"
        coords = [[float(coord) for coord in xy.split(",")] for xy in attrib["shape"].split(" ")]
        self.alignment = LineString(coords)
        self.shape = self.alignment.buffer(self.width/2, cap_style=CAP_STYLE.flat)
        self.parentEdge = None
        self.stop_offsets = []
        self.incoming_connections = []
        self.outgoing_connections = []
        self.requests = []  # type: list[_Request]

    def lane_type(self):
        """
        Returns a string descriptor of the type of lane, based on vehicle permissions.

        :return: lane type
        """
        if self.allows == "pedestrian":
            if self.parentEdge is not None and self.parentEdge.function == "crossing":
                return "crosswalk"
            else:
                return "pedestrian"
        if self.allows == "bicycle":
            return "bicycle"
        if self.allows == "ship":
            return "ship"
        if self.allows == "authority":
            return "authority"
        if self.allows == "none":
            return "none"
        if not self.allows["passenger"]:
            return "no_passenger"
        else:
            return "other"

    def lane_color(self):
        """
        Returns the Sumo-GUI default lane color for this lane.

        :return: lane color
        """
        type = self.lane_type()
        return COLOR_SCHEME[type] if type in COLOR_SCHEME else COLOR_SCHEME["other"]

    def plot_alignment(self, ax):
        """
        Plots the centerline alignment of the lane

        :param ax: matplotlib Axes object
        :return: None
        :type ax: plt.Axes
        """
        x, y = zip(*self.alignment.coords)
        ax.plot(x, y)

    def plot_shape(self, ax, **kwargs):
        """
        Plots the entire shape of the lane

        :param ax: matplotlib Axes object
        :return: None
        :type ax: plt.Axes
        """
        if "lw" not in kwargs and "linewidth" not in kwargs:
            kwargs["lw"] = 0
        poly = matplotlib.patches.Polygon(self.shape.boundary.coords, True, color=self.lane_color(), **kwargs)
        ax.add_patch(poly)

    def inverse_lane_index(self):
        """
        Returns the inverted lane index (i.e. counting from inside out)

        :return: inverted lane index
        """
        return self.parentEdge.lane_count() - self.index - 1

    def append_stop_offset(self, attrib):
        value = float(attrib["value"])
        vc = attrib["vClasses"] if "vClasses" in attrib else ""
        exceptions = attrib["exceptions"] if "exceptions" in attrib else ""
        vClasses = _Utils.Allowance(allow_string=vc, disallow_string=exceptions)
        self.stop_offsets.append((value, vClasses))

    def get_stop_line_locations(self):
        if len(self.stop_offsets) > 0:
            stop_offsets = self.stop_offsets
        else:
            stop_offsets = self.parentEdge.stop_offsets if self.parentEdge is not None else []
        stop_line_locations = []
        accrued_vClasses = _Utils.Allowance("none")
        for stop_offset, vClasses in stop_offsets:
            accrued_vClasses += vClasses
            stop_line_locations.append(stop_offset)
        if not accrued_vClasses.is_superset_of(self.allows) and 0 not in stop_line_locations:
            stop_line_locations.append(0)
        return stop_line_locations

    def _requires_stop_line(self):
        if self.parentEdge.to_junction.type in ["internal", "zipper"]:
            return False
        if self.parentEdge.to_junction.type == "always_stop":
            return True
        for request in self.requests:
            if "1" in request.response:
                return True
        return False

    def _get_marking_3d_description(self, marking, z=0.001):
        """
        Generates 3D vertices and faces for export of lane markings to OBJ format.

        :param z: the desired z coordinate for the lane markings. Defaults to 0.001.
        :return: vertex coordinates, faces (as lists of vertex indices)
        :type z: float
        """
        if marking["dashes"][1] == 0:  # if solid line
            buffer = marking["line"].buffer(marking["lw"]/2, cap_style=CAP_STYLE.flat)
            if buffer.geometryType() == "MultiPolygon":
                outlines = [polygon.boundary.coords for polygon in buffer]
            elif buffer.geometryType() == "Polygon":
                outlines = [buffer.boundary.coords]
            else:
                raise TypeError("Unexpected geometry type " + buffer.geometryType() + " created by buffer operation.")
            for vertices_2d in outlines:
                vertices = [[v[0], v[1], z] for v in vertices_2d]
                faces = [[i+1 for i in range(len(vertices))]]
            return vertices, faces
        else:  # if dashed line
            vertices, faces = [], []
            dash_length, gap = marking["dashes"]
            vertex_count = 0
            for s in np.arange(0, marking["line"].length, dash_length+gap):
                assert hasattr(ops, "substring"), "Shapely>=1.7.0 is required for OBJ export of dashed lines."
                dash_segment = ops.substring(marking["line"], s, min(s+dash_length, marking["line"].length))
                buffer = dash_segment.buffer(marking["lw"]/2, cap_style=CAP_STYLE.flat)
                if buffer.geometryType() == "MultiPolygon":
                    outlines = [polygon.boundary.coords for polygon in buffer]
                elif buffer.geometryType() == "Polygon":
                    outlines = [buffer.boundary.coords]
                else:
                    raise TypeError(
                        "Unexpected geometry type " + buffer.geometryType() + " created by buffer operation.")
                for outline in outlines:
                    vertices += [[v[0], v[1], z] for v in outline]
                    faces.append([i+vertex_count+1 for i in range(len(outline))])
                    vertex_count += len(outline)
            return vertices, faces

    def generate_markings_obj_text(self, vertex_count=0):
        """
        Generates Wavefront-OBJ file contents for this lane's markings, assuming vertex_count previous vertices.

        :param vertex_count: number of vertices already present in OBJ file.
        :return: obj text contents, new vertex_count
        :type vertex_count: int
        """
        content = ""
        for i, marking in enumerate(self._guess_lane_markings()):
            vertices, faces = self._get_marking_3d_description(marking)
            content += "o " + self.id + "_marking" + str(i)
            content += "\nusemtl marking_" + marking["color"]
            content += "\nv " + "\nv ".join([" ".join([str(c) for c in vertex]) for vertex in vertices])
            content += "\nf " + "\nf ".join([" ".join([str(v + vertex_count) for v in face]) for face in faces])
            content += "\n\n"
            vertex_count += len(vertices)
        return content, vertex_count

    def _get_3d_description(self, z=0, extrude_height=0, include_bottom_face=False):
        """
        Generates 3D vertices and faces for export to OBJ format.

        :param z: the desired z coordinate for the base of the object. Defaults to zero.
        :param extrude_height: distance by which to extrude the face vertically.
        :param include_bottom_face: whether or not to include the bottom face of the extruded geometry.
        :return: vertex coordinates, faces (as lists of vertex indices)
        :type z: float
        :type extrude_height: float
        :type include_bottom_face: bool
        """
        vertices_2d = self.shape.boundary.coords
        top_vertices, bottom_vertices = [], []
        for vertex in vertices_2d:
            bottom_vertices.append([vertex[0], vertex[1], z])
            top_vertices.append([vertex[0], vertex[1], z+extrude_height])
        vertices, faces = [], []
        vertices += top_vertices
        edge_size = len(top_vertices)
        faces += [[i+1 for i in range(edge_size)]]
        if extrude_height != 0:
            vertices += bottom_vertices
            faces += [[i+1, i+2, i+edge_size+2, i+edge_size+1] for i in range(edge_size-1)]
            if include_bottom_face:
                faces += [[i+edge_size+1 for i in range(edge_size)]]
        return vertices, faces

    def generate_obj_text(self, vertex_count=0):
        """
        Generates Wavefront-OBJ file contents for this object, assuming vertex_count previous vertices.

        :param vertex_count: number of vertices already present in OBJ file.
        :return: obj text contents, new vertex_count
        :type vertex_count: int
        """
        content = ""
        h = 0.15 if self.allows == "pedestrian" else 0
        vertices, faces = self._get_3d_description(extrude_height=h)
        content += "o " + self.id
        content += "\nusemtl " + self.lane_type()
        content += "\nv " + "\nv ".join([" ".join([str(c) for c in vertex]) for vertex in vertices])
        content += "\nf " + "\nf ".join([" ".join([str(v + vertex_count) for v in face]) for face in faces])
        content += "\n\n"
        vertex_count += len(vertices)
        return content, vertex_count

    def _draw_lane_marking(self, ax, line, width, color, dashes, **kwargs):
        try:
            x, y = zip(*line.coords)
            line = _Utils.LineDataUnits(x, y, linewidth=width, color=color, dashes=dashes, **kwargs)
            ax.add_line(line)
        except NotImplementedError:
            print("Can't print center stripe for lane " + self.id)
        except ValueError:
            print("Generated lane marking geometry is empty for lane " + self.id)

    def _guess_lane_markings(self):
        """
        Guesses lane markings based on lane configuration and globally specified lane marking style.

        :return: dict containing the marking alignment, line width, color, and dash pattern.
        """
        markings = []
        if self.parentEdge.function == "internal" or self.allows == "ship" or self.allows == "rail":
            return markings
        if self.parentEdge.function == "crossing":
            color, dashes = "w", (0.5, 0.5)
            markings.append({"line": self.alignment, "lw": self.width, "color": color, "dashes": dashes})
            return markings
        # US-style markings
        if LANE_MARKINGS_STYLE == USA_STYLE:
            lw = 0.1 * STRIPE_WIDTH_SCALE_FACTOR
            # Draw centerline stripe if necessary
            if self.inverse_lane_index() == 0:
                leftEdge = self.alignment.parallel_offset(self.width/2-lw, side="left")
                color, dashes = "y", (100, 0)
                markings.append({"line": leftEdge, "lw": lw, "color": color, "dashes": dashes})
            # Draw non-centerline markings
            else:
                adjacent_lane = self.parentEdge.get_lane(self.index+1)
                leftEdge = self.alignment.parallel_offset(self.width/2, side="left")
                color, dashes = "w", (3, 9)  # set default settings
                if self.allows("bicycle") != adjacent_lane.allows("bicycle"):
                    dashes = (100, 0)  # solid line where bicycles may not change lanes
                elif self.allows("passenger") != adjacent_lane.allows("passenger"):
                    if self.allows("bicycle"):
                        dashes = (1, 3)  # short dashed line where bikes may change lanes but passenger vehicles not
                    else:
                        dashes = (100, 0)  # solid line where neither passenger vehicles nor bikes may not change lanes
                markings.append({"line": leftEdge, "lw": lw, "color": color, "dashes": dashes})
            # draw outer lane marking if necessary
            if self.index == 0 and not (self.allows("pedestrian") and not self.allows("all")):
                rightEdge = self.alignment.parallel_offset(self.width/2, side="right")
                color, dashes = "w", (100, 0)
                markings.append({"line": rightEdge, "lw": lw, "color": color, "dashes": dashes})
        # European-style markings
        elif LANE_MARKINGS_STYLE == EUR_STYLE:
            lw = 0.1 * STRIPE_WIDTH_SCALE_FACTOR
            # Draw centerline stripe if necessary
            if self.inverse_lane_index() == 0:
                leftEdge = self.alignment.parallel_offset(self.width/2, side="left")
                color, dashes = "w", (100, 0)
                markings.append({"line": leftEdge, "lw": lw, "color": color, "dashes": dashes})
            # Draw non-centerline markings
            else:
                adjacent_lane = self.parentEdge.get_lane(self.index + 1)
                leftEdge = self.alignment.parallel_offset(self.width / 2, side="left")
                color, dashes = "w", (3, 9)  # set default settings
                if self.allows("bicycle") != adjacent_lane.allows("bicycle"):
                    dashes = (100, 0)  # solid line where bicycles may not change lanes
                elif self.allows("passenger") != adjacent_lane.allows("passenger"):
                    if self.allows("bicycle"):
                        dashes = (1, 3)  # short dashed line where bikes may change lanes but passenger vehicles not
                    else:
                        dashes = (100, 0)  # solid line where neither passenger vehicles nor bikes may not change lanes
                markings.append({"line": leftEdge, "lw": lw, "color": color, "dashes": dashes})
            # draw outer lane marking if necessary
            if self.index == 0 and not (self.allows("pedestrian") and not self.allows("all")):
                rightEdge = self.alignment.parallel_offset(self.width / 2, side="right")
                color, dashes = "w", (100, 0)
                markings.append({"line": rightEdge, "lw": lw, "color": color, "dashes": dashes})
        # Stop line markings (all styles)
        slw = 0.5
        if self.allows not in ["pedestrian", "ship"] and self._requires_stop_line():
            for stop_line_location in self.get_stop_line_locations():
                assert hasattr(ops, "substring"), "Shapely>=1.7.0 is required for drawing stop lines."
                pos = self.alignment.length - stop_line_location - slw/2
                end_cl = ops.substring(self.alignment, pos-1, pos)
                end_left = end_cl.parallel_offset(self.width / 2, side="left")
                end_right = end_cl.parallel_offset(self.width / 2, side="right")
                stop_line = LineString([end_left.coords[-1], end_right.coords[0]])
                markings.append({"line": stop_line, "lw": slw, "color": "w", "dashes": (100, 0)})
        return markings

    def plot_lane_markings(self, ax, **kwargs):
        """
        Guesses and plots some simple lane markings.

        :param ax: matplotlib Axes object
        :return: None
        :type ax: plt.Axes
        """
        for marking in self._guess_lane_markings():
            self._draw_lane_marking(ax, marking["line"], marking["lw"], marking["color"], marking["dashes"], **kwargs)


class _Connection:
    def __init__(self, attrib, parent_net=None):
        """
        Initialize a _Connection object.

        :param attrib: dict of all of the connection attributes
        :param parent_net: parent Net object. Used to access the referenced Lane objects.
        :type attrib: dict
        :type parent_net: Net
        """
        self.from_edge = attrib["from"]
        self.to_edge = attrib["to"]
        self.from_lane = attrib["fromLane"]
        self.to_lane = attrib["toLane"]
        self.via = attrib["via"] if "via" in attrib else None
        self.dir = attrib["dir"]
        self.state = attrib["state"]
        self.parent_net = parent_net

        if "shape" in attrib:
            coords = [[float(coord) for coord in xy.split(",")] for xy in attrib["shape"].split(" ")]
            self.shape = LineString(coords)
        else:
            self.shape = None

    def _generate_shape(self):
        """
        Generate the shape of the lane in two dimensions based on the from_lane, via_lane, and to_lane.

        The alignment is taken from the via_lane, with the extruded points being adjusted to match the corners of the
        from_lane and to_lane. The width of the Connection is taken from the from_lane.

        :return: Polygon of the Connection shape
        """
        if type(self.parent_net) != Net:
            raise ReferenceError("Valid reference to parent network required.")
        # Get relevant lane objects
        via_lane = self.parent_net._get_lane(self.via)  # type: _Lane
        from_lane = self.parent_net._get_edge(self.from_edge).get_lane(int(self.from_lane))  # type: _Lane
        to_lane = self.parent_net._get_edge(self.to_edge).get_lane(int(self.to_lane))  # type: _Lane
        # Get lane edges
        from_lane_left_edge = [list(c) for c in from_lane.alignment.parallel_offset(from_lane.width/2, side="left").coords]
        from_lane_right_edge = [list(c) for c in from_lane.alignment.parallel_offset(from_lane.width/2, side="right").coords]
        to_lane_left_edge = [list(c) for c in to_lane.alignment.parallel_offset(to_lane.width/2, side="left").coords]
        to_lane_right_edge = [list(c) for c in to_lane.alignment.parallel_offset(to_lane.width/2, side="right").coords]
        left_edge = [list(c) for c in via_lane.alignment.parallel_offset(from_lane.width/2, side="left").coords]
        right_edge = [list(c) for c in via_lane.alignment.parallel_offset(from_lane.width/2, side="right").coords]
        right_edge.reverse()
        # Generate coordinates
        left_coords = [from_lane_left_edge[-1]] + left_edge[1:-1] + [to_lane_left_edge[0]]
        right_coords = [from_lane_right_edge[0]] + right_edge[1:-1] + [to_lane_right_edge[-1]]
        left_coords.reverse()
        boundary_coords = right_coords + left_coords + [right_coords[0]]
        return Polygon(boundary_coords)

    def _get_3d_description(self, z=0, extrude_height=0, include_bottom_face=False):
        """
        Generates 3D vertices and faces for export to OBJ format.

        :param z: the desired z coordinate for the base of the object. Defaults to zero.
        :param extrude_height: distance by which to extrude the face vertically.
        :param include_bottom_face: whether or not to include the bottom face of the extruded geometry.
        :return: vertex coordinates, faces (as lists of vertex indices)
        :type z: float
        :type extrude_height: float
        :type include_bottom_face: bool
        """
        boundary_coords = self._generate_shape().boundary.coords
        # Perform extrusion
        top_vertices, bottom_vertices = [], []
        for vertex in boundary_coords:
            bottom_vertices.append([vertex[0], vertex[1], z])
            top_vertices.append([vertex[0], vertex[1], z+extrude_height])
        vertices, faces = [], []
        vertices += top_vertices
        edge_size = len(top_vertices)
        faces += [[i+1 for i in range(edge_size)]]
        if extrude_height != 0:
            vertices += bottom_vertices
            faces += [[i+1, i+2, i+edge_size+2, i+edge_size+1] for i in range(edge_size-1)]
            if include_bottom_face:
                faces += [[i+edge_size+1 for i in range(edge_size)]]
        return vertices, faces

    def generate_obj_text(self, vertex_count=0):
        """
        Generates Wavefront-OBJ file contents for this object, assuming vertex_count previous vertices.

        :param vertex_count: number of vertices already present in OBJ file.
        :return: obj text contents, new vertex_count
        :type vertex_count: int
        """
        content = ""
        via_lane = self.parent_net._get_lane(self.via)
        from_lane = self.parent_net._get_edge(self.from_edge).get_lane(int(self.from_lane))
        to_lane = self.parent_net._get_edge(self.to_edge).get_lane(int(self.to_lane))
        h = 0.15 if from_lane.lane_type() == "pedestrian" and to_lane.lane_type() == "pedestrian" else 0
        material = "pedestrian" if from_lane.lane_type() == "pedestrian" and to_lane.lane_type() == "pedestrian" else "connection"
        vertices, faces = self._get_3d_description(extrude_height=h)
        content += "o " + via_lane.id
        content += "\nusemtl " + material
        content += "\nv " + "\nv ".join([" ".join([str(c) for c in vertex]) for vertex in vertices])
        content += "\nf " + "\nf ".join([" ".join([str(v + vertex_count) for v in face]) for face in faces])
        content += "\n\n"
        vertex_count += len(vertices)
        return content, vertex_count

    def plot_alignment(self, ax):
        """
        Plot the centerline of the connection.
        :param ax: matplotlib Axes object
        :return: None
        :type ax: plt.Axes
        """
        if self.shape:
            x, y = zip(*self.shape.coords)
            ax.plot(x, y)


class _Request:
    def __init__(self, attrib, parent_junction=None):
        """
        Initializes a Request object

        :param attrib: dict of xml attributes
        :param parent_junction: parent Junction of this Request
        :type attrib: dict
        :type parent_junction: _Junction
        """
        self.index = int(attrib["index"])
        self.response = attrib["response"]
        self.foes = attrib["foes"]
        self.cont = attrib["cont"]
        self.parentJunction = parent_junction


class _Junction:
    def __init__(self, attrib):
        """
        Initializes a Junction object.

        :param attrib: dict of junction attributes.
        :type attrib: dict
        """
        self.id = attrib["id"]
        self.type = attrib["type"]
        self.incLane_ids = attrib["incLanes"].split(" ") if attrib["incLanes"] != "" else []
        self.intLane_ids = attrib["intLanes"].split(" ") if attrib["intLanes"] != "" else []
        self.incLanes = []
        self.intLanes = []
        self._requests = []
        self.shape = None
        if "shape" in attrib:
            coords = [[float(coord) for coord in xy.split(",")] for xy in attrib["shape"].split(" ")]
            if len(coords) > 2:
                self.shape = Polygon(coords)

    def append_request(self, request):
        request.parentJunction = self
        self._requests.append(request)

    def get_request_by_index(self, index):
        for req in self._requests:
            if req.index == index:
                return req
        raise IndexError("Junction " + self.id + " has no request with index " + str(index))

    def get_request_by_int_lane(self, lane_id):
        try:
            index = self.intLane_ids.index(lane_id)
        except ValueError as err:
            raise IndexError("Junction " + self.id + " does not include lane " + lane_id) from err
        else:
            return self.get_request_by_index(index)

    def generate_obj_text(self, vertex_count=0):
        """
        Generates Wavefront-OBJ file contents for this object, assuming vertex_count previous vertices.

        :param vertex_count: number of vertices already present in OBJ file.
        :return: obj text contents, new vertex_count
        :type vertex_count: int
        """
        vertices_2d = self.shape.boundary.coords
        vertices = [[vertex[0], vertex[1], 0] for vertex in vertices_2d]
        face = [i+1 for i in range(len(vertices))]
        content = ""
        content += "o " + self.id
        content += "\nusemtl junction"
        content += "\nv " + "\nv ".join([" ".join([str(c) for c in vertex]) for vertex in vertices])
        content += "\nf " + " ".join([str(v + vertex_count) for v in face])
        content += "\n\n"
        vertex_count += len(vertices)
        return content, vertex_count

    def plot(self, ax, **kwargs):
        """
        Plots the Junction.

        :param ax: matplotlib Axes object
        :return: None
        :type ax: plt.Axes
        """
        if self.shape is not None:
            if "lw" not in kwargs and "linewidth" not in kwargs:
                kwargs["lw"] = 0
            poly = matplotlib.patches.Polygon(self.shape.boundary.coords, True, color=COLOR_SCHEME["junction"], **kwargs)
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
        self.connections = []
        net = ET.parse(file).getroot()
        for obj in net:
            if obj.tag == "edge":
                if "function" in obj.attrib and obj.attrib["function"] == "walkingarea":
                    continue
                edge = _Edge(obj.attrib)
                for edgeChild in obj:
                    if edgeChild.tag == "stopOffset":
                        edge.append_stop_offset(edgeChild.attrib)
                    elif edgeChild.tag == "lane":
                        lane = _Lane(edgeChild.attrib)
                        for laneChild in edgeChild:
                            if laneChild.tag == "stopOffset":
                                lane.append_stop_offset(laneChild.attrib)
                        edge.append_lane(lane)
                self.edges.append(edge)
            elif obj.tag == "junction":
                junction = _Junction(obj.attrib)
                for jnChild in obj:
                    if jnChild.tag == "request":
                        req = _Request(jnChild.attrib)
                        junction.append_request(req)
                self.junctions.append(junction)
            elif obj.tag == "connection":
                connection = _Connection(obj.attrib, self)
                self.connections.append(connection)
        self._link_objects()

    def _link_objects(self):
        for edge in self.edges:
            edge.from_junction = self._get_junction(edge.from_junction_id)
            edge.to_junction = self._get_junction(edge.to_junction_id)
        for junction in self.junctions:
            if junction.type == "internal":
                continue
            for i in junction.incLane_ids:
                incLane = self._get_lane(i)
                if incLane is not None:
                    junction.incLanes.append(incLane)
            for i in junction.intLane_ids:
                intLane = self._get_lane(i)
                if i is not None:
                    junction.intLanes.append(intLane)
            for lane in junction.incLanes:
                lane.incoming_connections = self._get_connections_from_lane(lane.id)
                lane.outgoing_connections = self._get_connections_from_lane(lane.id)
                for cxn in self._get_connections_from_lane(lane.id):
                    if cxn.via is not None:
                        reqs = []
                        try:
                            req = junction.get_request_by_int_lane(cxn.via)
                        except IndexError:  # if no request found for via, look one level deeper
                            cxns_internal = self._get_connections_from_lane(cxn.via)
                            for cxni in cxns_internal:
                                req = junction.get_request_by_int_lane(cxni.via)
                                reqs.append(req)
                        else:
                            reqs.append(req)
                        for req in reqs:
                            lane.requests.append(req)

    def _get_extents(self):
        lane_geoms = []
        for edge in self.edges:
            for lane in edge.lanes:
                lane_geoms.append(lane.shape)
        polygons = MultiPolygon(lane_geoms)
        return polygons.bounds

    def _get_junction(self, junction_id):
        for junction in self.junctions:
            if junction.id == junction_id:
                return junction

    def _get_connections_from_lane(self, lane_id):
        cxns = []
        for connection in self.connections:
            if connection.from_edge + "_" + connection.from_lane == lane_id:
                cxns.append(connection)
        return cxns

    def _get_connections_to_lane(self, lane_id):
        cxns = []
        for connection in self.connections:
            if connection.to_edge + "_" + connection.to_lane == lane_id:
                cxns.append(connection)
        return cxns

    def _get_connections_via_lane(self, via):
        cxns = []
        for connection in self.connections:
            if connection.via == via:
                cxns.append(connection)
        return cxns

    def _get_edge(self, edge_id):
        for edge in self.edges:
            if edge.id == edge_id:
                return edge

    def _get_lane(self, lane_id):
        edge_id = "_".join(lane_id.split("_")[:-1])
        lane_num = int(lane_id.split("_")[-1])
        edge = self._get_edge(edge_id)
        return edge.get_lane(lane_num) if edge is not None else None

    def generate_obj_text(self, style=None, stripe_width_scale=1):
        """
        Generates the contents for a Wavefront-OBJ file which represents the network as a 3D model.

        This text can be saved as text to a file with the *.obj extension and then imported into a 3D modelling program.
        The axis configuration in the generated file is Y-Forward, Z-Up.

        :param style: lane marking style to use for rendering ("USA" or "EUR"). Defaults to last used or "EUR".
        :param stripe_width_scale: scale factor for lane striping widths. Defaults to 1.
        :return: None
        :type style: str
        :type stripe_width_scale: float
        """
        if style is not None:
            set_style(style)
        set_stripe_width_scale(stripe_width_scale)
        content = ""
        vertex_count = 0
        for edge in self.edges:
            if edge.function == "internal":
                continue
            for lane in edge.lanes:
                if edge.function not in ["crossing", "walkingarea"]:
                    lane_content, vertex_count = lane.generate_obj_text(vertex_count)
                    content += lane_content
                markings_content, vertex_count = lane.generate_markings_obj_text(vertex_count=vertex_count)
                content += markings_content
        for junction in self.junctions:
            if junction.shape is not None:
                junction_content, vertex_count = junction.generate_obj_text(vertex_count)
                content += junction_content
        for connection in self.connections:
            if connection.via is not None:
                via_lane = self._get_lane(connection.via)
                from_lane = self._get_edge(connection.from_edge).get_lane(int(connection.from_lane))
                to_lane = self._get_edge(connection.to_edge).get_lane(int(connection.to_lane))
                if from_lane.lane_type() == "pedestrian" and to_lane.lane_type() == "pedestrian":
                    lane_content, vertex_count = connection.generate_obj_text(vertex_count)
                    content += lane_content
        return content

    def plot(self, ax=None, clip_to_limits=False, zoom_to_extents=True, style=None, stripe_width_scale=1,
             lane_kwargs=None, lane_marking_kwargs=None, junction_kwargs=None, **kwargs):
        """
        Plots the Net. Kwargs are passed to the plotting functions, with object-specific kwargs overriding general ones.

        :param ax: matplotlib Axes object. Defaults to current axes.
        :param clip_to_limits: if True, only objects in the current view will be drawn. Speeds up saving of animations.
        :param zoom_to_extents: if True, window will be set to the network extents. Ignored if clip_to_limits is True
        :param style: lane marking style to use for plotting ("USA" or "EUR"). Defaults to last used or "EUR".
        :param stripe_width_scale: scale factor for lane striping widths
        :param lane_kwargs: kwargs to pass to the lane plotting function (matplotlib.patches.Polygon())
        :param lane_marking_kwargs: kwargs to pass to the lane markings plotting function (matplotlib.lines.Line2D())
        :param junction_kwargs: kwargs to pass to the junction plotting function (matplotlib.patches.Polygon())
        :return: None
        :type ax: plt.Axes
        :type clip_to_limits: bool
        :type zoom_to_extents: bool
        :type style: str
        :type stripe_width_scale: float
        """
        if style is not None:
            set_style(style)
        set_stripe_width_scale(stripe_width_scale)
        if ax is None:
            ax = plt.gca()
        if junction_kwargs is None:
            junction_kwargs = dict()
        if lane_kwargs is None:
            lane_kwargs = dict()
        if lane_marking_kwargs is None:
            lane_marking_kwargs = dict()
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
            if edge.function != "internal" and (not clip_to_limits or edge.intersects(window)):
                edge.plot(ax, {"zorder": -100, **lane_kwargs}, {"zorder": -90, **lane_marking_kwargs}, **kwargs)
        for junction in self.junctions:
            if not clip_to_limits or (junction.shape is not None and junction.shape.intersects(window)):
                junction.plot(ax, **{"zorder": -110, **kwargs, **junction_kwargs})


if __name__ == "__main__":
    net = Net('../Sample/test.net.xml')
    fig, ax = plt.subplots()
    # ax.set_facecolor("green")
    net.plot(ax, style=USA_STYLE, stripe_width_scale=3)
    plt.show()
