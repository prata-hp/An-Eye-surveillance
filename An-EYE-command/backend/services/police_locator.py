from math import asin
from math import cos
from math import radians
from math import sin
from math import sqrt

import requests


OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

REQUEST_HEADERS = {
    "User-Agent": "AN-EYE/1.0 local-dispatch-discovery",
    "Accept": "application/json",
}


def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(
        radians,
        [lon1, lat1, lon2, lat2],
    )

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * asin(sqrt(a))

    return 6371 * c


def _element_coordinates(element):
    if "lat" in element and "lon" in element:
        return element["lat"], element["lon"]

    center = element.get("center")

    if center:
        return center["lat"], center["lon"]

    return None, None


def get_nearby_police_stations(lat, lng, radius=5000):
    query = f"""
    [out:json][timeout:20];
    (
      node["amenity"="police"](around:{radius},{lat},{lng});
      way["amenity"="police"](around:{radius},{lat},{lng});
      relation["amenity"="police"](around:{radius},{lat},{lng});
    );
    out body center;
    """

    last_error = None

    for overpass_url in OVERPASS_URLS:
        try:
            response = requests.post(
                overpass_url,
                data={"data": query},
                headers=REQUEST_HEADERS,
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            break
        except requests.RequestException as exc:
            last_error = exc
    else:
        raise last_error

    stations = []
    seen = set()

    for element in data.get("elements", []):
        station_lat, station_lng = _element_coordinates(element)

        if station_lat is None or station_lng is None:
            continue

        tags = element.get("tags", {})
        name = (
            tags.get("name")
            or tags.get("name:en")
            or "Unnamed Police Station"
        )

        key = (
            name,
            round(station_lat, 5),
            round(station_lng, 5),
        )

        if key in seen:
            continue

        seen.add(key)

        distance = haversine(
            lat,
            lng,
            station_lat,
            station_lng,
        )

        stations.append(
            {
                "name": name,
                "latitude": station_lat,
                "longitude": station_lng,
                "distance_km": round(distance, 2),
                "source": "OpenStreetMap",
            }
        )

    stations.sort(key=lambda station: station["distance_km"])

    return stations[:5]
