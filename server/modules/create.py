import atexit
from pathlib import Path
from modules import tee, audio, youtube, video, streams, monitor


FOLDER = str(Path("./data/").resolve())


def create_file_stream(filename: str, display: monitor.MonitorDisplay):
    filepath = str(Path(FOLDER, filename).resolve())
    if not filepath.startswith(FOLDER):
        raise ValueError("Path Travesal")

    f = open(filepath, "rb")
    datastream_1, datastream_2 = tee.tee(f)

    res = video.get_video_resolution(filepath)
    video_stream = video.stream_video(
        stream=datastream_1,
        resolution=res,
        display=display,
    )
    audio_stream = audio.stream_audio(datastream_2)

    return streams.create_stream(
        display=display,
        video=video_stream,
        audio=audio_stream,
        onclose=lambda: f.close(),
    )


def create_youtube_stream(id: str, display: monitor.MonitorDisplay) -> str | None:
    url = f"https://www.youtube.com/watch?v={id}"
    result = youtube.get_youtube_stream(url)
    if not result:
        return None

    datastream_1, datastream_2 = tee.tee(result.stream)

    video_stream = video.stream_video(
        stream=datastream_1,
        resolution=result.resolution,
        display=display,
    )
    audio_stream = audio.stream_audio(datastream_2)
    stream_id = streams.create_stream(
        display=display,
        video=video_stream,
        audio=audio_stream,
        onclose=lambda: result.process.kill(),
    )
    return stream_id


def create_livestream_stream(display: monitor.MonitorDisplay) -> str:
    video_stream = video.stream_livestream(video.DISPLAY)
    return streams.create_stream(display, video_stream)
