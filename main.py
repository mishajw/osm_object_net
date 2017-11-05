import argparse
import item
import logging
import osm_map


def main():
    parser = argparse.ArgumentParser("osm_object_net")
    parser.add_argument("--osm_path", type=str, help="The path of the .osm file to parse", default="data/map.osm")
    args = parser.parse_args()

    _map = osm_map.parse(args.osm_path)

    output_items = item.parse(_map)

    [print(_item) for _item in output_items]

    item.make_image(output_items, 1080, 1080, "images/test.png")


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    main()
