import typing as t
import numpy as np

from encode import encode_numpy_frame, encode_pillow_frame, MonitorDisplay
import encode

import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import time
import cv2
import pyautogui

DISPLAY = MonitorDisplay(
    monitorWidth=36,
    monitorHeight=24,
    monitorColumns=11,
    monitorRows=6
)


def stream_video(filepath: str, display: MonitorDisplay) -> t.Generator[str]:
    frames = opencv_stream_video_frames(filepath)

    with ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
        for frame in frames:
            yield encode_numpy_frame(display, frame, executor)


def opencv_stream_video_frames(filepath: str) -> t.Generator[np.ndarray]:
    i = -1
    cap = cv2.VideoCapture(filepath)
    while True:
        ret, frame = cap.read()
        i += 1
        if not ret:
            break

        if cv2.waitKey(0) == ord("q"):
            break

        if i % 3 == 0:
            continue

        yield frame


import io
def ffmpeg_stream_video_frames(filepath: str) -> t.Generator[np.ndarray]:
    with open(filepath, "rb") as f:
        buffer = io.BytesIO(f.read(100_000))

    decoder = FFdecoder(buffer)
    buffer.seek(0)
    decoder.formulate(buffer)

    firstFrame = next(decoder.generateFrame())
    decoder.terminate()


    sourceSize = (firstFrame.shape[1], firstFrame.shape[0])
    displaySize = encode.calculate_display_size(DISPLAY)
    newSize, _ = encode.calculate_resize_parameters(sourceSize, displaySize)

    ffparams = {
        "-vf": f"scale={newSize[0]}:{newSize[1]},fps=20",
    }

    with open(filepath, "rb") as f:
        decoder = FFdecoder(source=f, **ffparams)
        f.seek(0)
        decoder.formulate(f)

    yield from decoder.generateFrame()


def stream_livestream(display: MonitorDisplay) -> t.Generator[str]:
    with ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
        start = time.time()
        i = 0
        while True:
            img = pyautogui.screenshot()
            i += 1
            yield encode_pillow_frame(display, img, executor)
            print((time.time() - start) / i)


def stream_noise() -> t.Generator[str]:
    with ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
        start = time.time()
        i = 0
        while True:
            im_arr = np.random.rand(500,500,3) * 255
            yield encode_numpy_frame(DISPLAY, im_arr, executor)
