import uuid
import time

from deepface import DeepFace

from .face_extractor import extract_face_from_clip
from .suspect_registry import (
    load_suspects,
    save_suspects
)
from .suspect_matcher import (
    find_matching_suspect
)


MATCH_THRESHOLD = 0.75


def process_suspect(video_path):

    print("\n[Suspect] Processing Started...")

    # ------------------------------------
    # STEP 1 — Extract face from clip
    # ------------------------------------

    face_path = extract_face_from_clip(video_path)

    if not face_path:

        print("[Suspect] No face detected.")
        return

    print("[Suspect] Face extracted.")

    # ------------------------------------
    # STEP 2 — Generate embedding
    # ------------------------------------

    try:

        embedding_data = DeepFace.represent(
            img_path=face_path,
            model_name="Facenet",
            enforce_detection=False
        )

        embedding = embedding_data[0]["embedding"]

    except Exception as e:

        print("[Suspect] Embedding Error:", e)
        return

    print("[Suspect] Embedding generated.")

    # ------------------------------------
    # STEP 3 — Load suspect database
    # ------------------------------------

    suspects = load_suspects()

    # ------------------------------------
    # STEP 4 — Match with existing suspects
    # ------------------------------------

    match, score = find_matching_suspect(
        embedding,
        suspects
    )

    current_time = time.strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    # ------------------------------------
    # STEP 5 — Existing suspect found
    # ------------------------------------

    if match and score > MATCH_THRESHOLD:

        print(f"[Suspect] MATCH FOUND")
        print(f"[Suspect] Similarity: {score:.2f}")

        match["violence_count"] += 1
        match["last_seen"] = current_time

        # Risk logic

        count = match["violence_count"]

        if count >= 3:
            match["risk_level"] = "HIGH"

        elif count >= 2:
            match["risk_level"] = "MEDIUM"

        else:
            match["risk_level"] = "LOW"

        save_suspects(suspects)

        print(f"[Suspect] Updated count: {count}")
        print(f"[Suspect] Risk: {match['risk_level']}")

    # ------------------------------------
    # STEP 6 — New suspect
    # ------------------------------------

    else:

        suspect = {

            "suspect_id": str(uuid.uuid4())[:8],

            "face_image": face_path,

            "embedding": embedding,

            "violence_count": 1,

            "risk_level": "LOW",

            "first_seen": current_time,

            "last_seen": current_time
        }

        suspects.append(suspect)

        save_suspects(suspects)

        print("[Suspect] New suspect created.")