import json
from pathlib import Path

CAMERA_FILE = Path("backend/data/cameras.json")


def load_cameras():
    with open(CAMERA_FILE, "r") as f:
        return json.load(f)


def get_camera(camera_id):
    cameras = load_cameras()

    for camera in cameras:
        if camera["camera_id"] == camera_id:
            return camera

    return None