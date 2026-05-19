import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv(
    "SUPABASE_BUCKET",
    "incident-clips"
)


def get_supabase_client():

    if not SUPABASE_URL or not SUPABASE_KEY:

        raise RuntimeError(
            "Set SUPABASE_URL and SUPABASE_KEY before uploading clips."
        )

    return create_client(
        SUPABASE_URL,
        SUPABASE_KEY,
    )


def upload_clip(file_path):

    supabase = get_supabase_client()

    file_name = os.path.basename(file_path)

    with open(file_path, "rb") as f:

        supabase.storage.from_(SUPABASE_BUCKET).upload(
            file_name,
            f,
            file_options={
                "upsert": "true",
            },
        )

    public_url = supabase.storage.from_(
        SUPABASE_BUCKET
    ).get_public_url(file_name)

    return public_url