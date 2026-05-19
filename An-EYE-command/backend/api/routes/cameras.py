import json

from fastapi import APIRouter


router = APIRouter(tags=["cameras"])


@router.get("/cameras")
def get_cameras():
    with open("config/cameras.json", "r") as file:
        return json.load(file)
