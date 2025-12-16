import typing as t
import multiprocessing as mp
from concurrent.futures import ThreadPoolExecutor
import pyautogui

from modules.encoder import encode_frame, display


def stream_livestream(display: display.MonitorDisplay) -> t.Iterator[bytes]:
    with ThreadPoolExecutor(max_workers=mp.cpu_count()) as executor:
        while True:
            img = pyautogui.screenshot()
            yield encode_frame(display, img, executor)
