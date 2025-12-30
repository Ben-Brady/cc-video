import ccv
import typing as t
import subprocess as sp
from itertools import batched
import json

from .display import MonitorDisplay
from .tee import tee

MARGIN = (0,0,0,0)

def stream_video(stream: t.IO[bytes], display: MonitorDisplay) -> t.Iterator[bytes]:
    ffprobe_io, ffmpeg_io = tee(stream)
    res = get_video_resolution(ffprobe_io)
    frame_stream = start_ffmpeg_stream(ffmpeg_io, res)

    for batch in batched(frame_stream, 10):
        ccv_display = ccv.MonitorDisplay(
            grid=(display.rows, display.columns),
            monitor=(display.monitorWidth, display.monitorHeight),
            margin=MARGIN
        )
        images = [
            ccv.Image(width=res[0], height=res[1], data=frame)
            for frame in batch
        ]
        yield from ccv.encode_frames(images, ccv_display)


def get_video_resolution(
    stream: t.IO[bytes],
) -> tuple[int, int]:
    cmd = ["ffprobe"]
    cmd += ["-v", "quiet"]
    cmd += ["-show_streams"]
    cmd += ["-print_format", "json"]
    cmd += ["-"]

    process = sp.Popen(cmd, stdin=stream, stdout=sp.PIPE, stderr=sp.DEVNULL)
    data = process.stdout.read().decode()  # type: ignore
    info = json.loads(data)

    assert "streams" in info, "Could not find streams"
    video_streams = [
        stream for stream in info["streams"] if stream["codec_type"] == "video"
    ]

    assert len(video_streams) > 0, "No video stream found"
    vstream = t.cast(dict[str, int], video_streams[0])

    assert "width" in vstream, "width not found"
    width = vstream["width"]

    assert "height" in vstream, "height not found"
    height = vstream["height"]

    return width, height


def start_ffmpeg_stream(
    stream: t.IO[bytes], res: tuple[int, int]
) -> t.Iterator[bytes]:
    cmd = ["ffmpeg"]
    cmd += ["-i", "-"]
    cmd += ["-vf", f"fps=fps=20"]
    cmd += ["-f", "rawvideo"]
    cmd += ["-pix_fmt", "rgb24"]
    cmd += ["-"]

    process = sp.Popen(cmd, stdin=stream, stdout=sp.PIPE, stderr=sp.DEVNULL)

    while True:
        width, height = res
        size = width * height * 3
        data = process.stdout.read(size)  # type: ignore
        if len(data) < size:
            return

        yield data

