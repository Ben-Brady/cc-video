import typing as t
from fastapi import FastAPI, WebSocket, Query, Response
from tqdm import tqdm
from pathlib import Path
from random import randint, sample
import uvicorn

import video, audio
import json
from dataclasses import dataclass

app = FastAPI()

FILEPATH = "./data/nostalgia.mp4"
# FILEPATH = "./data/dance.mov"

FOLDER = Path("D:/Hydrus/Memes/client_files")

FILES = []
for dir in FOLDER.iterdir():
    for file in dir.iterdir():
        if file.name.endswith("mp4"):
            FILES.append(file)

@dataclass
class Stream:
    display: video.MonitorDisplay
    video: t.Generator[str]
    audio: t.Generator[str] | None

streams: dict[int, Stream] = {}

@app.get("/start/stream")
async def _():
    id = randint(0, 2 ** 16)
    stream = Stream(
        display=video.DISPLAY,
        video=video.stream_livestream(video.DISPLAY),
        audio=None
    )
    streams[id] = stream
    return id

@app.get("/start/video")
async def _():
    id = randint(0, 2 ** 16)
    filepath = FILEPATH
    # filepath = sample(FILES,k=1)[0]
    stream = Stream(
        display=video.DISPLAY,
        video=video.stream_video(filepath, video.DISPLAY),
        audio=audio.stream_video_file(filepath, 20)
    )
    streams[id] = stream
    return id


@app.websocket("/video")
async def _(websocket: WebSocket, id: int = Query()):
    if id not in streams:
        return Response(status_code=404)

    await websocket.accept()
    stream = streams[id].video

    while True:
        try:

            batch_size = int(await websocket.receive_text())
            for _ in range(batch_size):
                frame = next(stream)
                await websocket.send_text(frame)
        except StopIteration:
            await websocket.send_text("END")
            break


@app.websocket("/audio")
async def _(websocket: WebSocket, id: int = Query()):
    if id not in streams:
        return Response(status_code=404)

    stream = streams[id].audio
    if not stream:
        return Response(status_code=400)

    await websocket.accept()

    while True:
        try:
            batch_size = int(await websocket.receive_text())
            for _ in range(batch_size):
                frame = next(stream)
                data = json.dumps(frame)
                await websocket.send_text(data)
        except StopIteration:
            await websocket.send_text("END")
            break



if __name__ == "__main__":
    # video_frames = list(tqdm(video.stream_video(FILEPATH, video.DISPLAY), total=3500))
    # audio_frames = list(tqdm(audio.stream_video_file(FILEPATH, 20)))
    uvicorn.run(app, port=8000)
