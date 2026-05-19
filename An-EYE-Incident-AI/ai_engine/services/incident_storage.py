import json
import os


def save_incident(incident):
    os.makedirs("storage/incidents", exist_ok=True)

    file_path = f"storage/incidents/{incident.incident_id}.json"

    with open(file_path, "w") as file:
        json.dump(
            incident.dict(),
            file,
            indent=4,
            default=str,
        )

    return file_path
