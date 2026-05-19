import time
import cv2

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

import uvicorn

import streaming.frame_buffer as frame_buffer


app = FastAPI()

templates = Jinja2Templates(
    directory="streaming/templates"
)


@app.get("/")
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )


def generate_frames():

    while True:

        if frame_buffer.latest_frame is None:
            time.sleep(0.01)
            continue

        frame = frame_buffer.latest_frame.copy()

        ret, buffer = cv2.imencode(".jpg", frame)

        if not ret:
            continue

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes +
            b"\r\n"
        )


@app.get("/video_feed")
def video_feed():

    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


if __name__ == "__main__":

    uvicorn.run(
        "streaming.stream_server:app",
        host="0.0.0.0",
        port=8001,
        reload=False
    )