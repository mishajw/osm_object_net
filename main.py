import argparse
import logging.config
import osm_map


def main():
    parser = argparse.ArgumentParser("osm_object_net")
    parser.add_argument("--osm_path", type=str, help="The path of the .osm file to parse", default="data/map.osm")
    args = parser.parse_args()

    parse_results = osm_map.parse(args.osm_path)

    parse_results.attribute_analysis()
    print("done")


if __name__ == "__main__":
    try:
        logging.config.fileConfig("logging.ini")
    except KeyError:
        logging.basicConfig()

    main()
