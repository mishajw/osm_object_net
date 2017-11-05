import argparse
import logging
import osm_map


def main():
    parser = argparse.ArgumentParser("osm_object_net")
    parser.add_argument("--osm_path", type=str, help="The path of the .osm file to parse", default="data/map.osm")
    args = parser.parse_args()

    parse_results = osm_map.parse(args.osm_path)

    parse_results.attribute_analysis()


if __name__ == "__main__":
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    main()
