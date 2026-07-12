import json


def read_geojson(input_file):
    with open(input_file, "r", encoding="utf-8") as file:
        return json.load(file)
