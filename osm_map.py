from typing import Dict, List, NamedTuple, Callable
from xml.etree import ElementTree
import logging

log = logging.getLogger(__name__)

parsable_tags = ["node", "way"]

Node = NamedTuple("OsmNode", [("id", int), ("attributes", Dict[str, str])])

Way = NamedTuple("OsmWay", [("id", int), ("nodes", List[Node]), ("attributes", Dict[str, str])])


class Map:
    def __init__(self) -> None:
        # TODO: do we need this now we've got `__node_dict`?
        self.__nodes: List[Node] = []
        self.__ways: List[Way] = []

        # Maps from node id to nodes for quick lookup
        self.__node_dict: Dict[int, Node] = {}

    def add_node(self, node: Node):
        self.__nodes.append(node)
        self.__node_dict[node.id] = node

    def get_node(self, node_id: int):
        return self.__node_dict[node_id]

    def add_way(self, way: Way):
        self.__ways.append(way)

    def get_nodes(self):
        return self.__nodes

    def get_ways(self):
        return self.__ways

    def attribute_analysis(self):
        def analyse_list(l):
            attribute_counts: Dict[str, int] = {}

            for element in l:
                for key in element.attributes:
                    if key in attribute_counts:
                        attribute_counts[key] += 1
                    else:
                        attribute_counts[key] = 1

            for key in attribute_counts:
                log.info(f"Found {attribute_counts[key]} occurrences of {key}")

        log.info("Nodes:")
        analyse_list(self.__nodes)
        log.info("Ways:")
        analyse_list(self.__ways)


def parse(osm_path: str) -> Map:
    _map = Map()

    map_iter = ElementTree.iterparse(osm_path, events=("start", "end"))

    current_element: ElementTree.Element = None
    current_element_children: List[ElementTree.Element] = []

    for event, element in map_iter:
        if current_element is None and event == "start" and element.tag in parsable_tags:
            log.debug(f"Started parsable element {element}")

            current_element = element

        elif event == "end" and element == current_element:
            log.debug(f"Finished element {element}")

            __handle_element(current_element, current_element_children, _map)

            log.debug("Resetting current element")
            current_element = None
            current_element_children = []

        elif current_element is not None:
            log.debug(f"Adding {element} as child of {current_element}")

            current_element_children.append(element)

        else:
            log.warning(f"Unhandled element {element}")

    return _map


def __handle_element(
        element: ElementTree.Element, children: List[ElementTree.Element], _map: Map) -> None:

    log.debug(f"Handling element {element} with children {children}")

    if element.tag == "node":
        _map.add_node(__handle_node(element, children))
    if element.tag == "way":
        _map.add_way(__handle_way(element, children, _map.get_node))
    else:
        log.warning(f"Saw unknown tag type in element {element}")


def __handle_node(node_element: ElementTree.Element, node_children: List[ElementTree.Element]) -> Node:
    attributes = node_element.attrib

    # Get the ID from the attributes
    node_id = __extract_id(attributes)

    # Add children - we assume they are all tag nodes
    attributes.update(__tag_elements_to_dict(node_children))

    return Node(node_id, attributes)


def __handle_way(
        way_element: ElementTree.Element,
        way_children: List[ElementTree.Element],
        get_node_fn: Callable[[int], Node]) -> Way:

    attributes = way_element.attrib

    # Get the ID from the attributes
    way_id = __extract_id(attributes)

    tags: List[ElementTree.Element] = []
    nodes: List[Node] = []

    for child in way_children:
        if child.tag == "tag":
            tags.append(child)

        elif child.tag == "nd":
            assert list(child.attrib.keys()) == ["ref"]
            node_id = int(child.attrib["ref"])
            nodes.append(get_node_fn(node_id))

    # Add children - we assume they are all tag nodes
    attributes.update(__tag_elements_to_dict(tags))

    return Way(way_id, nodes, attributes)


def __extract_id(attributes: Dict[str, str]) -> int:
    # Get the id from the attributes then remove it from the dict
    assert "id" in attributes
    element_id = int(attributes["id"])
    attributes.pop("id")

    return element_id


def __tag_elements_to_dict(tag_elements: List[ElementTree.Element]) -> Dict[str, str]:
    tag_dict: Dict[str, str] = {}

    for element in tag_elements:
        assert element.tag == "tag"

        if set(element.attrib.keys()) != {"k", "v"}:
            log.warning(f"Couldn't parse tag element {element} that had attribs {element.attrib}")

        tag_dict[element.attrib["k"]] = element.attrib["v"]

    return tag_dict
