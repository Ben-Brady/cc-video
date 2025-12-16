import typing as t
import numpy as np
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import pyautogui

from modules.encoder import encode_numpy_frame, encode_pillow_frame, display


def stream_livestream(display: display.MonitorDisplay) -> t.Iterator[bytes]:
    with ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
        while True:
            img = pyautogui.screenshot()
            yield encode_pillow_frame(display, img, executor)


def stream_noise(display: display.MonitorDisplay) -> t.Iterator[bytes]:
    with ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
        while True:
            im = np.random.rand(500, 500, 3) * 255
            yield encode_numpy_frame(display, im, executor)
