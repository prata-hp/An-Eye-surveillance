import json
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Path to cameras.json
CAMERA_FILE = BASE_DIR / "config" / "cameras.json"


def load_cameras():
    """
    Load all camera data
    """

    with open(CAMERA_FILE, "r") as file:
        cameras = json.load(file)

    return cameras


def get_camera(camera_id):
    """
    Get camera by camera_id
    """

    cameras = load_cameras()

    for camera in cameras:
        if camera["camera_id"] == camera_id:
            return camera

    raise ValueError(f"Camera '{camera_id}' not found")