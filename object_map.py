from typing import Union, List
import logging
import osm_map

log = logging.getLogger(__name__)


class Coords:
    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon

    @classmethod
    def from_osm(cls, osm: Union[osm_map.OsmNode, osm_map.OsmWay]):
        assert "lat" in osm.attributes
        assert "lon" in osm.attributes
        return Coords(float(osm.attributes["lat"]), float(osm.attributes["lon"]))


class Item:
    def __init__(self, _id: int):
        self.id = _id


class NodeBasedItem(Item):
    @classmethod
    def from_node(cls, node: osm_map.OsmNode):
        raise NotImplementedError()


class WayBasedItem(Item):
    @classmethod
    def from_way(cls, node: osm_map.OsmWay):
        raise NotImplementedError()


class Tree(NodeBasedItem):
    def __init__(self, _id: int, coords: Coords):
        super().__init__(_id)
        self.coords = coords

    @classmethod
    def from_node(cls, node: osm_map.OsmNode):
        assert "natural" in node.attributes
        assert node.attributes["natural"] == "tree"

        coords = Coords.from_osm(node)

        return Tree(node.id, coords)


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


node_based_items = __get_subclasses(NodeBasedItem)
way_based_items = __get_subclasses(WayBasedItem)


def parse(input_map: osm_map.OsmMap) -> List[Item]:
    def parse_list(l: Union[List[osm_map.OsmNode], List[osm_map.OsmWay]], classes) -> List[Item]:
        for element in l:
            for element_class in classes:
                try:
                    log.debug(f"Trying to parse {element} as {element_class}")
                    yield element_class.from_node(element)
                    break
                except AssertionError as e:
                    log.debug(f"Couldn't due to {e}")

    node_items = parse_list(input_map.get_nodes(), node_based_items)
    way_items = parse_list(input_map.get_ways(), node_based_items)

    return list(node_items) + list(way_items)
