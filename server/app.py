from fastapi import FastAPI, WebSocket, Query, Response
import uvicorn
from modules import create, streams, monitor


app = FastAPI()


@app.websocket("/stream/video")
async def _(websocket: WebSocket, id: str = Query()):
    with streams.aqquire_stream(id) as stream:
        await websocket.accept()

        while True:
            try:
                batch_size = int(await websocket.receive_text())
                for _ in range(batch_size):
                    frame = next(stream.video)
                    await websocket.send_text(frame)
            except StopIteration:
                await websocket.send_text("END")
                return


@app.websocket("/stream/audio")
async def _(websocket: WebSocket, id: str = Query()):
    with streams.aqquire_stream(id) as stream:
        if not stream.audio:
            print(f"Stream audio '{id}' not found")
            return Response(status_code=400)

        await websocket.accept()

        while True:
            try:
                batch_size = int(await websocket.receive_text())
                for _ in range(batch_size):
                    frame = next(stream.audio)
                    await websocket.send_text(frame)
            except StopIteration:
                await websocket.send_text("END")
                return


@app.get("/start/stream")
async def _(display_str: str = Query(alias="display")):
    display = monitor.MonitorDisplay.from_display_string(display_str)
    if not display:
        return Response(status_code=400)

    return create.create_livestream_stream(display)


@app.get("/start/file")
async def _(filename: str = Query(), display_str: str = Query(alias="display")):
    display = monitor.MonitorDisplay.from_display_string(display_str)
    if not display:
        return Response(status_code=400)

    stream_id = create.create_file_stream(filename, display)
    return stream_id


@app.get("/start/youtube")
async def _(id: str = Query(), display_str: str = Query(alias="display")):
    display = monitor.MonitorDisplay.from_display_string(display_str)
    if not display:
        return Response(status_code=400)

    stream_id = create.create_youtube_stream(id, display)

    if not stream_id:
        return Response(status_code=404)
    else:
        return stream_id


if __name__ == "__main__":
    uvicorn.run(app, port=8000)
