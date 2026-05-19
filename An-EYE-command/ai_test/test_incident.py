import uuid
from datetime import UTC
from datetime import datetime

import requests

from upload_to_cloud import upload_clip


BACKEND_URL = "http://127.0.0.1:8000/incidents"
VIDEO_PATH = "../testor.mp4"


print("Uploading clip...")

clip_url = upload_clip(VIDEO_PATH)

print("Uploaded:", clip_url)

random_suffix = str(uuid.uuid4())[:8]

incident_data = {
    "incident_id": str(uuid.uuid4()),
    "camera_id": f"CAM-{random_suffix}",
    "city": "Patna",
    "precinct": "South Belt",
    "location": f"Test Zone {random_suffix}",
    "latitude": 25.6196,
    "longitude": 85.1622,
    "timestamp": datetime.now(UTC).isoformat(),
    "confidence": 0.96,
    "violence_type": "Physical Assault",
    "clip_path": clip_url,
    "thumbnail_path": "",
    "status": "NEW",
    "priority_score": 96.0,
}

response = requests.post(
    BACKEND_URL,
    json=incident_data,
)

print(response.json())
