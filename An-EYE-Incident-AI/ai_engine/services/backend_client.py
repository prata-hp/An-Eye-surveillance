import os

import requests
from dotenv import load_dotenv


load_dotenv()


BACKEND_URL = os.getenv("BACKEND_URL")


if not BACKEND_URL:
    raise ValueError(
        "BACKEND_URL missing in .env"
    )


def send_incident(incident):

    try:

        response = requests.post(
            f"{BACKEND_URL}/incidents",
            json=incident,
            timeout=10,
        )

        response.raise_for_status()

        print("\n[Backend] Incident sent")
        print(response.json())

        return response.json()

    except requests.exceptions.RequestException as e:

        print("\n[Backend] Connection failed")
        print(e)

        return None