import typing as t
import numpy as np
import subprocess as sp
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import json

from .frame import (
    _encode_numpy_frame,
    caclulate_target_res,
)
from .display import MonitorDisplay
from .tee import tee


def stream_video(stream: t.IO[bytes], display: MonitorDisplay) -> t.Iterator[bytes]:
    ffprobe_io, ffmpeg_io = tee(stream)
    res = get_video_resolution(ffprobe_io)

    targetRes = caclulate_target_res(res, display)
    frame_stream = start_ffmpeg_stream(ffmpeg_io, targetRes)

    with ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
        for frame in frame_stream:
            yield _encode_numpy_frame(display, frame, executor)


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
) -> t.Iterator[np.ndarray]:
    width, height = res

    cmd = ["ffmpeg"]
    cmd += ["-i", "-"]
    cmd += ["-vf", f"scale={width}:{height},fps=fps=20"]
    cmd += ["-f", "rawvideo"]
    cmd += ["-pix_fmt", "rgb24"]
    cmd += ["-"]

    process = sp.Popen(cmd, stdin=stream, stdout=sp.PIPE, stderr=sp.DEVNULL)

    while True:
        size = width * height * 3
        data = process.stdout.read(size)  # type: ignore
        if len(data) < size:
            return

        arr_1d = np.frombuffer(data, dtype=np.uint8)
        arr = arr_1d.reshape(height, width, 3)
        yield arr
