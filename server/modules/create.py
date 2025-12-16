import typing as t
import itertools
from pathlib import Path
from modules import youtube, video, streams
from modules.encoder import display, tee
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
        onclose=lambda: f.close(),
    )


def create_youtube_stream(id: str, display: display.MonitorDisplay) -> str | None:
    url = f"https://www.youtube.com/watch?v={id}"
    result = youtube.get_youtube_stream(url)
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
        onclose=lambda: result.process.kill(),
    )
    return stream_id


def create_livestream_stream(display: display.MonitorDisplay) -> str:
    video_stream = video.stream_livestream(display)
    return streams.create_stream(display, video_stream)
