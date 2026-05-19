import cv2
import os
from deepface import DeepFace

OUTPUT_DIR = "ai_engine/suspect_faces"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def extract_face_from_clip(video_path):

    cap = cv2.VideoCapture(video_path)

    frame_count = 0

    best_face_path = None

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame_count += 1

        # check every 20th frame
        if frame_count % 20 != 0:
            continue

        try:

            faces = DeepFace.extract_faces(
                img_path=frame,
                detector_backend="opencv",
                enforce_detection=False
            )

            if len(faces) > 0:

                face = faces[0]["face"]

                filename = os.path.join(
                    OUTPUT_DIR,
                    f"suspect_{frame_count}.jpg"
                )

                face = (face * 255).astype("uint8")

                cv2.imwrite(filename, face)

                best_face_path = filename

                print(f"[Face] Saved: {filename}")

                break

        except Exception as e:
            print("[Face Error]", e)

    cap.release()

    return best_face_path