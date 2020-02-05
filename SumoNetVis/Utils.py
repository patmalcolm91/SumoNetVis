"""
Contains miscellaneous utility classes and functions for internal library use.
"""

from matplotlib.lines import Line2D

VEHICLE_CLASS_LIST = ["private", "emergency", "authority", "army", "vip", "pedestrian", "passenger", "hov", "taxi",
                      "bus", "coach", "delivery", "truck", "trailer", "motorcycle", "moped", "bicycle", "evehicle",
                      "tram", "rail_urban", "rail", "rail_electric", "rail_fast", "ship", "custom1", "custom2"]


def invert_lane_allowance(allow):
    """
    Calculates the corresponding disallow string for a given allow string (or vice versa).
    :param allow: the allow string
    :return: the disallow string
    """
    if allow == "all":
        return ""
    allow = allow.split(" ")
    disallow = []
    for vClass in VEHICLE_CLASS_LIST:
        if vClass not in allow:
            disallow.append(vClass)
    return " ".join(disallow)


class LineDataUnits(Line2D):
    """
    A Line2D object, but with the linewidth and dash properties defined in data coordinates.
    """
    def __init__(self, *args, **kwargs):
        _lw_data = kwargs.pop("linewidth", 1)
        _dashes_data = kwargs.pop("dashes", (1,))
        super().__init__(*args, **kwargs)
        self._lw_data = _lw_data
        self._dashes_data = _dashes_data

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
            return tuple([((trans((1, dash_data))-trans((0, 0)))*ppd)[1] for dash_data in self._dashes_data])
        else:
            return tuple((1, 0))

    def _set_dashes(self, dashes):
        self._dashes_data = dashes

    _linewidth = property(_get_lw, _set_lw)
    _dashSeq = property(_get_dashes, _set_dashes)
