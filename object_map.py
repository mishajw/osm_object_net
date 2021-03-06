from enum import Enum
from typing import Union, List, Dict, Optional
import logging
import osm_map

log = logging.getLogger(__name__)


class StringEnum(Enum):
    @classmethod
    def contains_str(cls, s: str) -> bool:
        names = [road_type.name.lower() for road_type in cls]
        return s in names

    @classmethod
    def get_from_str(cls, s: str):
        for road_type in cls:
            if s == road_type.name.lower():
                return road_type

        return None


class Coords:
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon

    @classmethod
    def from_node(cls, node: osm_map.Node):
        assert "lat" in node.attributes
        assert "lon" in node.attributes
        return Coords(float(node.attributes["lat"]), float(node.attributes["lon"]))

    @classmethod
    def list_from_way(cls, way: osm_map.Way):
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
    def from_node(cls, node: osm_map.Node):
        raise NotImplementedError()


class WayBasedItem(Item):
    def __init__(self, _id: int, all_coords: List[Coords]):
        super().__init__(_id)
        self.all_coords = all_coords

    @classmethod
    def from_way(cls, way: osm_map.Way):
        raise NotImplementedError()


class Tree(NodeBasedItem):
    def __init__(self, _id: int, coords: Coords):
        super().__init__(_id, coords)

    @classmethod
    def from_node(cls, node: osm_map.Node):
        assert "natural" in node.attributes
        assert node.attributes["natural"] == "tree"

        coords = Coords.from_node(node)

        return Tree(node.id, coords)


class Road(WayBasedItem):
    class RoadType(StringEnum):
        Residential = 0
        Footway = 1

    def __init__(self, _id: int, all_coords: List[Coords], road_type: RoadType):
        super().__init__(_id, all_coords)
        self.road_type = road_type

    @classmethod
    def from_way(cls, way: osm_map.Way):
        assert "highway" in way.attributes
        assert Road.RoadType.contains_str(way.attributes["highway"])

        return Road(way.id, Coords.list_from_way(way), Road.RoadType.get_from_str(way.attributes["highway"]))


class Building(WayBasedItem):
    class BuildingType(StringEnum):
        YES = 0
        HOUSE = 1
        RESIDENTIAL = 2
        APARTMENTS = 3
        GARAGE = 4
        GARAGES = 5

    def __init__(self, _id: int, all_coords: List[Coords], house_type: BuildingType):
        super().__init__(_id, all_coords)
        self.house_type = house_type

    @classmethod
    def from_way(cls, way: osm_map.Way):
        assert "building" in way.attributes
        assert Building.BuildingType.contains_str(way.attributes["building"])

        return Building(
            way.id, Coords.list_from_way(way), Building.BuildingType.get_from_str(way.attributes["building"]))


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


def parse(_map: osm_map.Map) -> List[Item]:
    def parse_osm_element(element: Union[osm_map.Node, osm_map.Way], creators) -> Optional[Item]:
        for element_creator in creators:
            try:
                return element_creator(element)
            except AssertionError:
                pass

        log.warning(f"Couldn't parse {element} as any type")
        return None

    def parse_list(l: Union[List[osm_map.Node], List[osm_map.Way]], classes) -> List[Item]:
        parse_attempts = [parse_osm_element(element, classes) for element in l]
        return [item_opt for item_opt in parse_attempts if item_opt is not None]

    node_items = parse_list(_map.get_nodes(), node_based_creators)
    way_items = parse_list(_map.get_ways(), way_based_creators)

    return list(node_items) + list(way_items)
