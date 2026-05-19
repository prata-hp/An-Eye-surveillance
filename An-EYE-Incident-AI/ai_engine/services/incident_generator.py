import uuid
from datetime import datetime


def generate_incident(
    camera_data,
    confidence,
    violence_type,
    clip_path,
    thumbnail_path=None,
):

    incident = {

        "incident_id": str(uuid.uuid4()),

        "camera_id": camera_data["camera_id"],

        "city": camera_data["city"],

        "precinct": camera_data["precinct"],

        "location": camera_data["location"],

        "latitude": camera_data["latitude"],

        "longitude": camera_data["longitude"],

        "camera_status": "ONLINE",

        "timestamp": datetime.utcnow().isoformat(),

        "created_at": datetime.utcnow().isoformat(),

        "confidence": float(confidence),

        "violence_type": violence_type,

        "clip_path": clip_path,

        "thumbnail_path": thumbnail_path or "",

        "status": "NEW",

        "priority_score": float(confidence * 100),
    }

    return incident