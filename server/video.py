import typing as t
import numpy as np

from encode import encode_numpy_frame, encode_pillow_frame, MonitorDisplay

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


def stream_video(filepath: str | int, display: MonitorDisplay) -> t.Generator[str]:
    frames = stream_video_frames(filepath)

    with ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
        for i, frame in enumerate(frames):
            if i % 3 == 0:
                continue

            yield encode_numpy_frame(display, frame, executor)


def stream_video_frames(filepath: str | int) -> t.Generator[np.ndarray]:
    cap = cv2.VideoCapture(filepath)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if cv2.waitKey(0) == ord("q"):
            break

        yield frame

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
