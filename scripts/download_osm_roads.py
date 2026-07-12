import osmnx as ox
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
OUTPUT_FILE = PROJECT_DIR / "data" / "krakow_roads.geojson"

place = "Kraków, Poland"

print("Downloading real road data from OpenStreetMap...")
graph = ox.graph_from_place(place, network_type="drive")

nodes, edges = ox.graph_to_gdfs(graph)

edges = edges.reset_index()
edges = edges[["osmid", "name", "highway", "geometry"]]

edges.to_file(OUTPUT_FILE, driver="GeoJSON")

print(f"Saved real roads to: {OUTPUT_FILE}")
