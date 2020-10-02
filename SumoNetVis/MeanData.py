"""
Tools for dealing with Lane- and Edge-based traffic measure output files.
"""

import xml.etree.ElementTree as ET

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


class EdgeBasedMeasures():
    def __init__(self, files=None):
        self.data = dict()  # dict like {interval: data} where data is a dict like {edge_id: attributes_dict}
        if type(files) == str:
            self.load_file(files)
        elif files is not None:
            for file in files:
                self.load_file(file)

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
                    self.data[interval_tuple] = dict()
                self.data[interval_tuple].update({edge.attrib["id"]: edge.attrib})

    def __getitem__(self, item):
        for interval, interval_data in self.data.items():
            if interval[0] <= item < interval[1]:
                return interval_data
        raise IndexError("Time", item, "not contained in any interval.")

    def __iter__(self):
        return iter(sorted(self.data.keys()))


if __name__ == "__main__":
    edgeMeasures = EdgeBasedMeasures("../Sample/edgeBasedTest.xml")
    print(edgeMeasures[30])
