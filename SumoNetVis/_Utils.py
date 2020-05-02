"""
Contains miscellaneous utility classes and functions for internal library use.
"""

import numpy as np
from matplotlib.lines import Line2D


class Object3D:
    def __init__(self, name, material, vertices, faces):
        """
        Create a 3D object.

        :param name: name of the object
        :param material: name of the material to associate to the object
        :param vertices: list of vertex coordinates
        :param faces: list of faces, each a list of indices of the vertices making up the face
        :type name: str
        :type material: str
        :type vertices: list[list[float]]
        :type faces: list[list[int]]
        """
        self.vertices = vertices
        self.faces = faces
        self.name = name
        self.material = material

    @classmethod
    def from_shape(cls, shape, name, material, z=0, extrude_height=0, include_bottom_face=False):
        """
        Generates an Object3D from a shapely shape, either as a flat plane or by extrusion along the z axis

        :param shape: shapely Polygon or MultiPolygon from which to create 3D object
        :param name: name of the object
        :param material: name of the material to associate to the object
        :param z: the desired z coordinate for the base of the object. Defaults to zero.
        :param extrude_height: distance by which to extrude the face vertically.
        :param include_bottom_face: whether to include the bottom face of the extruded geometry.
        :type name: str
        :type material: str
        :type z: float
        :type extrude_height: float
        :type include_bottom_face: bool
        """
        vertices, faces = [], []
        # get coordinate sequences from shape
        if shape.geometryType() == "MultiPolygon":
            outlines = [polygon.boundary.coords for polygon in shape]
        elif shape.geometryType() == "Polygon":
            outlines = [shape.boundary.coords]
        else:
            raise NotImplementedError("Can't generate 3D object from " + shape.geometryType())
        # calculate vertices and faces
        for outline in outlines:
            # generate coordinates of top and bottom face
            top_vertices = [[v[0], v[1], z+extrude_height] for v in outline]
            v_offset = len(vertices)
            edge_len = len(top_vertices)
            # add top vertices and face
            vertices += top_vertices
            faces += [[i+1 for i in range(v_offset, v_offset+edge_len)]]
            # perform extrusion
            if extrude_height != 0:
                bottom_vertices = [[v[0], v[1], z] for v in outline]
                vertices += bottom_vertices
                # add side faces
                faces += [[i+1, i+2, i+edge_len+2, i+edge_len+1] for i in range(v_offset, v_offset+edge_len-1)]
                # add bottom face
                if include_bottom_face:
                    faces += [[i+edge_len+1 for i in range(v_offset, v_offset+edge_len)]]
        return cls(name, material, vertices, faces)


def generate_obj_text_from_objects(objects):
    """
    Generate Wavefront OBJ text from a list of Object3D objects

    :param objects: list of Object3D objects
    :return: Wavefront OBJ text
    :type objects: list[Object3D]
    """
    content = ""
    vertex_count = 0
    for object in objects:
        content += "o " + object.name
        content += "\nusemtl " + object.material
        content += "\nv " + "\nv ".join([" ".join([str(c) for c in vertex]) for vertex in object.vertices])
        content += "\nf " + "\nf ".join([" ".join([str(v + vertex_count) for v in face]) for face in object.faces])
        content += "\n\n"
        vertex_count += len(object.vertices)
    return content


class Allowance:
    """
    A class for handling vehicle class lane allowances.
    """
    vClass_list = np.array(
        ["private", "emergency", "authority", "army", "vip", "pedestrian", "passenger", "hov", "taxi",
         "bus", "coach", "delivery", "truck", "trailer", "motorcycle", "moped", "bicycle", "evehicle",
         "tram", "rail_urban", "rail", "rail_electric", "rail_fast", "ship", "custom1", "custom2"])

    def __init__(self, allow_string="all", disallow_string=""):
        """
        Initializes an Allowance object.

        :param allow_string: string containing space-separated list of allowed vehicle classes
        :param disallow_string: string containing space-separated list of disallowed vehicle classes
        :type allow_string: str
        :type disallow_string: str
        """
        if allow_string in ["all", ""]:
            allows = self.vClass_list
        elif allow_string == "none":
            allows = np.array([])
        else:
            allows = np.array(allow_string.split(" "))
        if disallow_string == "all":
            disallows = self.vClass_list
        elif disallow_string == "":
            disallows = np.full(len(self.vClass_list), False)
        else:
            disallows = np.array(disallow_string.split(" "))
        allow_mask = np.isin(self.vClass_list, allows)
        disallow_mask = np.isin(self.vClass_list, disallows)
        self.mask = np.logical_and(allow_mask, ~disallow_mask)

    def allows(self, vClass):
        """
        Checks if the specified vClass is allowed by this Allowance.

        :param vClass: vClass to check
        :return: True if vClass allowed, else False
        :type vClass: str
        """
        if vClass == "all":
            return self.mask.all()
        if vClass == "none":
            return np.logical_not(self.mask).all()
        if vClass not in self.vClass_list:
            raise IndexError("Invalid vehicle class " + str(vClass))
        return self.mask[np.where(self.vClass_list == vClass)[0]].all()

    def get_allow_string(self):
        """Return the 'allow' string as it would appear in a Net file."""
        if self.mask.all():
            return "all"
        elif not self.mask.any():
            return "none"
        else:
            return " ".join(self.vClass_list[self.mask])

    def get_disallow_string(self):
        """Return the 'disallow' string as it would appear in a Net file."""
        if self.mask.all():
            return "none"
        elif not self.mask.any():
            return "all"
        else:
            return " ".join(self.vClass_list[~self.mask])

    def is_superset_of(self, other):
        return self.mask[other.mask].all()

    def __getitem__(self, vClass):
        return self.allows(vClass)

    def __call__(self, *vClasses, operation="all"):
        if operation not in ["all", "any"]:
            raise ValueError("Invalid operation " + str(operation))
        op = np.all if operation == "all" else np.any
        return op([self.allows(vClass) for vClass in vClasses])

    def __invert__(self):
        inverted = Allowance()
        inverted.mask = ~self.mask
        return inverted

    def __eq__(self, other):
        if type(other) == str:
            other = type(self)(other)
        if type(other) == type(self):
            return np.array_equal(self.mask, other.mask)
        else:
            raise NotImplementedError("Can't compare " + str(type(self)) + " to " + str(type(other)))

    def __add__(self, other):
        if type(other) == str:
            other = type(self)(other)
        result = Allowance()
        result.mask = np.logical_or(self.mask, other.mask)
        return result

    def __repr__(self):
        return "Allowance('" + self.get_allow_string() + "')"


class LineDataUnits(Line2D):
    """
    A Line2D object, but with the linewidth and dash properties defined in data coordinates.
    """
    def __init__(self, *args, **kwargs):
        _lw_data = kwargs.pop("linewidth", 1)
        _dashes_data = kwargs.pop("dashes", (1, 0))
        super().__init__(*args, **kwargs)
        self.set_linestyle("--")
        self._lw_data = _lw_data
        self._dashes_data = _dashes_data
        self._dashOffset = 0

    def _get_lw(self):
        if self.axes is not None:
            ppd = 72./self.axes.figure.dpi
            trans = self.axes.transData.transform
            return ((trans((1, self._lw_data))-trans((0, 0)))*ppd)[1]
        else:
            return 1

    def _set_lw(self, lw):
        self._lw_data = lw

    def _get_dashes(self):
        if self.axes is not None:
            ppd = 72./self.axes.figure.dpi
            trans = self.axes.transData.transform
            dpu = (trans((1, 1)) - trans((0, 0)))[0]
            return tuple([u*dpu*ppd for u in self._dashes_data])
        else:
            return tuple((1, 0))

    def _set_dashes(self, dashes):
        self._dashes_data = dashes

    _linewidth = property(_get_lw, _set_lw)
    _dashSeq = property(_get_dashes, _set_dashes)
