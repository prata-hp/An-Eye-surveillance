from ai_engine.services.incident_generator import generate_incident
from ai_engine.services.incident_storage import save_incident
from ai_engine.utils.camera_loader import load_cameras


def main():
    cameras = load_cameras()

    camera = cameras[0]

    incident = generate_incident(
        camera_data=camera,
        confidence=0.91,
        violence_type="Physical Assault",
        clip_path="storage/clips/fight_01.mp4",
        thumbnail_path="storage/thumbnails/fight_01.jpg",
    )

    save_path = save_incident(incident)

    print("Incident Created")
    print(incident)

    print(f"Saved to: {save_path}")


if __name__ == "__main__":
    main()
