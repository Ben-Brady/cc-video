import ccv
import numpy as np
import typing as t
import multiprocessing as mp
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from modules import youtube, streams
from modules.encoder import display, tee, MARGIN
from modules.encoder import stream_video, stream_audio


FOLDER = str(Path("./data/").resolve())


def create_file_stream(filename: str, display: display.MonitorDisplay):
    filepath = str(Path(FOLDER, filename).resolve())
    if not filepath.startswith(FOLDER):
        raise ValueError("Path Travesal")

    f = open(filepath, "rb")
    datastream_1, datastream_2 = tee(f)

    video_stream = stream_video(
        stream=datastream_1,
        display=display,
    )
    audio_stream = stream_audio(datastream_2)

    return streams.create_stream(
        display=display,
        video=video_stream,
        audio=audio_stream,
        close=lambda: f.close(),
    )


def create_youtube_stream(id: str, display: display.MonitorDisplay) -> str | None:
    result = youtube.get_youtube_stream(id)
    if not result:
        return None

    datastream_1, datastream_2 = tee(result.stream)

    video_stream = stream_video(
        stream=datastream_1,
        display=display,
    )
    audio_stream = stream_audio(datastream_2)
    stream_id = streams.create_stream(
        display=display,
        video=video_stream,
        audio=audio_stream,
        close=result.close,
    )
    return stream_id


def create_livestream_stream(display: display.MonitorDisplay) -> str:
    import pyautogui

    def stream_livestream(display: display.MonitorDisplay) -> t.Iterator[bytes]:
        with ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
            while True:
                img = pyautogui.screenshot()
                ccv_img = ccv.Image(
                    width=img.width,
                    height=img.height,
                    data=np.array(img).flatten().tobytes()
                )
                ccv_display = ccv.MonitorDisplay(
                    grid=(display.columns,display.rows),
                    monitor=(display.monitorWidth, display.monitorHeight),
                    margin=MARGIN
                )
                yield ccv.encode_frame(ccv_img, ccv_display)

    video_stream = stream_livestream(display)
    return streams.create_stream(display, video_stream)
