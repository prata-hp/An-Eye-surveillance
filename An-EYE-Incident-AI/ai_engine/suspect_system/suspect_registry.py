import json
import os

DB_FOLDER = "ai_engine/suspect_db"
DB_FILE = os.path.join(DB_FOLDER, "suspects.json")

os.makedirs(DB_FOLDER, exist_ok=True)

if not os.path.exists(DB_FILE):

    with open(DB_FILE, "w") as f:
        json.dump([], f)


def load_suspects():

    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_suspects(data):

    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)