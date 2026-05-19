from math import atan2
from math import cos
from math import radians
from math import sin
from math import sqrt


def haversine_distance(lat1, lon1, lat2, lon2):
    radius_km = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a),
    )

    return radius_km * c


def find_nearest_stations(incident_lat, incident_lon, stations):
    station_distances = []

    for station in stations:
        distance = haversine_distance(
            incident_lat,
            incident_lon,
            station.latitude,
            station.longitude,
        )

        station_distances.append(
            {
                "station": station,
                "distance_km": round(distance, 2),
            }
        )

    station_distances.sort(key=lambda x: x["distance_km"])

    return station_distances[:3]
