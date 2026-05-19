import json
from pathlib import Path
from geopy.distance import geodesic

STATION_FILE = Path("backend/data/police_stations.json")


def load_stations():
    with open(STATION_FILE, "r") as f:
        return json.load(f)


def get_nearest_stations(lat, lng, limit=3):

    stations = load_stations()

    incident_coords = (lat, lng)

    results = []

    for station in stations:

        station_coords = (
            station["latitude"],
            station["longitude"]
        )

        distance = geodesic(
            incident_coords,
            station_coords
        ).km

        results.append({
            **station,
            "distance_km": round(distance, 2)
        })

    results.sort(key=lambda x: x["distance_km"])

    return results[:limit]