import typing as t
import numpy as np
import subprocess as sp
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import time
import pyautogui
import json

from modules.encode import encode_numpy_frame, encode_pillow_frame
from modules import monitor


def stream_video_from_file(
    filepath: str, display: monitor.MonitorDisplay
) -> t.Generator[str]:
    res = get_video_resolution(filepath)
    with open(filepath, "rb") as f:
        yield from stream_video(f, res, display)


def stream_video(
    stream: t.IO[bytes], resolution: tuple[int, int], display: monitor.MonitorDisplay
) -> t.Generator[str]:
    frames = ffmpeg_stream_video_frames(stream, resolution)
    with ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
        for frame in frames:
            yield encode_numpy_frame(display, frame, executor)


def stream_livestream(display: monitor.MonitorDisplay) -> t.Generator[str]:
    with ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
        start = time.time()
        i = 0
        while True:
            img = pyautogui.screenshot()
            i += 1
            yield encode_pillow_frame(display, img, executor)
            print((time.time() - start) / i)


def stream_noise(display: monitor.MonitorDisplay) -> t.Generator[str]:
    with ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
        while True:
            im = np.random.rand(500, 500, 3) * 255
            yield encode_numpy_frame(display, im, executor)


def get_video_resolution(filepath: str) -> tuple[int, int]:
    cmd = ["ffprobe"]
    cmd += [filepath]
    cmd += ["-hide_banner"]
    cmd += ["-show_format", "-show_streams"]
    cmd += ["-of", "json"]

    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.DEVNULL)
    data = p.stdout.read().decode()
    info = json.loads(data)
    for stream in info["streams"]:
        if stream["codec_type"] != "video":
            continue
        width = stream["width"]
        height = stream["height"]
        return width, height

    raise ValueError("cannot find video stream")


def ffmpeg_stream_video_frames(
    stream: t.IO[bytes], res: tuple[int, int]
) -> t.Iterable[np.ndarray]:
    width, height = res
    cmd = ["ffmpeg"]
    cmd += ["-i", "-"]
    cmd += ["-vf", f"scale={width}:{height},fps=fps=20"]
    cmd += ["-f", "rawvideo"]
    cmd += ["-pix_fmt", "rgb24"]
    cmd += ["-"]

    p = sp.Popen(cmd, stdin=stream, stdout=sp.PIPE, stderr=sp.DEVNULL)

    while True:
        size = width * height * 3
        data = p.stdout.read(size)
        if len(data) < size:
            return

        yield np.frombuffer(data, dtype=np.uint8).reshape(height, width, 3)
