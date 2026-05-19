import os
import subprocess


def convert_to_browser_format(input_path):

    base, _ = os.path.splitext(input_path)

    output_path = f"{base}_web.mp4"

    command = [
        "ffmpeg",
        "-y",
        "-i",
        input_path,
        "-vcodec",
        "libx264",
        "-acodec",
        "aac",
        "-movflags",
        "+faststart",
        output_path
    ]

    print("\n[FFmpeg] Converting clip to browser-compatible format...")

    subprocess.run(command, check=True)

    print(f"[FFmpeg] Conversion complete -> {output_path}")

    return output_path