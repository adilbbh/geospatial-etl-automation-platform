import json
from pathlib import Path

import folium

PROJECT_DIR = Path(__file__).resolve().parents[1]
INPUT_FILE = PROJECT_DIR / "data" / "roads.geojson"
OUTPUT_FILE = PROJECT_DIR / "output" / "roads_map.html"


with open(INPUT_FILE, "r", encoding="utf-8") as file:
    roads = json.load(file)

m = folium.Map(location=[50.064, 19.944], zoom_start=14)

folium.GeoJson(
    roads,
    name="Roads",
    tooltip=folium.GeoJsonTooltip(
        fields=["road_id", "road_name", "road_type"],
        aliases=["Road ID", "Road Name", "Road Type"],
    ),
).add_to(m)

folium.LayerControl().add_to(m)

OUTPUT_FILE.parent.mkdir(exist_ok=True)
m.save(OUTPUT_FILE)

print(f"Map created: {OUTPUT_FILE}")
