import argparse
import logging
import object_map
import osm_map


def main():
    parser = argparse.ArgumentParser("osm_object_net")
    parser.add_argument("--osm_path", type=str, help="The path of the .osm file to parse", default="data/map.osm")
    args = parser.parse_args()

    _map = osm_map.parse(args.osm_path)

    output_items = object_map.parse(_map)

    [print(item) for item in output_items]


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    main()
