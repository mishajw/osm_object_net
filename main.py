import xml.etree.ElementTree as et
import itertools
import logging
from typing import Dict, List, NamedTuple

log = logging.getLogger(__name__)

parsable_tags = ["node"]

Node = NamedTuple("Node", [("id", int), ("attributes", Dict[str, str])])

class ParseResults:
    def __init__(self) -> None:
        self.nodes: List[Node] = []

    def print_summary(self):
        print("Parse results summary")
        print("Nodes:")
        for node in self.nodes:
            print(f"{node.id} -> {node.attributes}")


def main():
    parse_results = ParseResults()

    map_iter = et.iterparse("data/map.osm", events=("start", "end"))
    map_iter = itertools.islice(map_iter, 100)

    current_element: et.Element = None
    current_element_children: List[et.Element] = []

    for event, element in map_iter:
        if current_element is None and event == "start" and element.tag in parsable_tags:
            log.debug(f"Started parsable element {element}")

            current_element = element

        elif event == "end" and element == current_element:
            log.debug(f"Finished element {element}")

            handle_element(current_element, current_element_children, parse_results)

            log.debug("Resetting current element")
            current_element = None
            current_element_children = []

        elif current_element is not None:
            log.debug(f"Adding {element} as child of {current_element}")

            current_element_children.append(element)

        else:
            log.warn(f"Unhandled element {element}")

    parse_results.print_summary()


def handle_element(
        element: et.Element, children: List[et.Element], parse_results: ParseResults) -> None:

    log.debug(f"Handling element {element} with children {children}")

    if element.tag == "node":
        parse_results.nodes.append(handle_node(element, children))
    else:
        log.warn(f"Saw unknown tag type in element {element}")


def handle_node(node_element: et.Element, node_children: List[et.Element]) -> Node:
    attributes = node_element.attrib

    # Get the ID from the attributes
    node_id = extract_id(attributes)

    # Add children - we assume they are all tag nodes
    attributes.update(tag_elements_to_dict(node_children))

    return Node(node_id, attributes)


def extract_id(attributes: Dict[str, str]) -> int:
    # Get the id from the attributes then remove it from the dict
    assert "id" in attributes
    element_id = int(attributes["id"])
    attributes.pop("id")

    return element_id


def tag_elements_to_dict(tag_elements: List[et.Element]) -> Dict[str, str]:
    tag_dict: Dict[str, str] = {}

    for element in tag_elements:
        assert element.tag == "tag"

        if set(element.attrib.keys()) != set(["k", "v"]):
            log.warn(f"Couldn't parse tag element {element} that had attribs {element.attrib}")

        tag_dict[element.attrib["k"]] = element.attrib["v"]

    return tag_dict


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    main()

