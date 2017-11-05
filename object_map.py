from enum import Enum
from typing import Union, List, Dict
import logging
import osm_map

log = logging.getLogger(__name__)


class Coords:
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon

    @classmethod
    def from_node(cls, node: osm_map.OsmNode):
        assert "lat" in node.attributes
        assert "lon" in node.attributes
        return Coords(float(node.attributes["lat"]), float(node.attributes["lon"]))

    @classmethod
    def list_from_way(cls, way: osm_map.OsmWay):
        # TODO this won't work
        return [Coords.from_node(node) for node in way.nodes]


class Item:
    def __init__(self, _id: int):
        self.id = _id


class NodeBasedItem(Item):
    def __init__(self, _id: int, coords: Coords):
        super().__init__(_id)
        self.coords = coords

    @classmethod
    def from_node(cls, node: osm_map.OsmNode):
        raise NotImplementedError()


class WayBasedItem(Item):
    def __init__(self, _id: int, all_coords: List[Coords]):
        super().__init__(_id)
        self.all_coords = all_coords

    @classmethod
    def from_way(cls, way: osm_map.OsmWay):
        raise NotImplementedError()


class Tree(NodeBasedItem):
    def __init__(self, _id: int, coords: Coords):
        super().__init__(_id, coords)

    @classmethod
    def from_node(cls, node: osm_map.OsmNode):
        assert "natural" in node.attributes
        assert node.attributes["natural"] == "tree"

        coords = Coords.from_node(node)

        return Tree(node.id, coords)


class Road(WayBasedItem):
    class RoadType(Enum):
        Residential = 0
        Footway = 1

    __road_type_dict: Dict[str, RoadType] = \
        dict([(road_type.name.lower(), road_type) for road_type in RoadType])

    def __init__(self, _id: int, all_coords: List[Coords], road_type: RoadType):
        super().__init__(_id, all_coords)
        self.road_type = road_type

    @classmethod
    def from_way(cls, way: osm_map.OsmWay):
        assert "highway" in way.attributes
        assert way.attributes["highway"] in Road.__road_type_dict.keys()

        return Road(way.id, Coords.list_from_way(way), Road.__road_type_dict[way.attributes["highway"]])


def __get_subclasses(cls):
    subclasses = set()
    work = [cls]

    while work:
        parent = work.pop()
        for child in parent.__subclasses__():
            if child not in subclasses:
                subclasses.add(child)
                work.append(child)

    return subclasses


node_based_creators = [subclass.from_node for subclass in __get_subclasses(NodeBasedItem)]
way_based_creators = [subclass.from_way for subclass in __get_subclasses(WayBasedItem)]


def parse(input_map: osm_map.OsmMap) -> List[Item]:
    def parse_list(l: Union[List[osm_map.OsmNode], List[osm_map.OsmWay]], classes) -> List[Item]:
        for element in l:
            for element_creator in classes:
                try:
                    log.debug(f"Trying to parse {element} as {element_creator}")
                    yield element_creator(element)
                    break
                except AssertionError as e:
                    log.debug(f"Couldn't due to {e}")

    node_items = parse_list(input_map.get_nodes(), node_based_creators)
    way_items = parse_list(input_map.get_ways(), way_based_creators)

    return list(node_items) + list(way_items)
