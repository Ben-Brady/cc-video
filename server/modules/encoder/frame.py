import typing as t
import numpy as np
from PIL import Image, ImagePalette
from concurrent.futures import ThreadPoolExecutor
from random import randint
import cv2
from contextlib import contextmanager
from . import display
from .bytes import ByteReader, ByteWriter
import time

T_MARGIN = 0
B_MARGIN = 0
L_MARGIN = 0
R_MARGIN = 0
# T_MARGIN = 3
# B_MARGIN = 4
# L_MARGIN = 3
# R_MARGIN = 3


averages: dict[str, list[float]] = {}


@contextmanager
def measure(name: str):
    averages.setdefault(name, [])

    start = time.time()
    yield
    duration = (time.time() - start) * 1000
    averages[name].append(duration)
    avg_duration = sum(averages[name]) / len(averages[name])
    print(f"{name}: {avg_duration:.1f}ms")


def encode_numpy_frame(
    display: display.MonitorDisplay,
    frame: np.ndarray,
    executor: ThreadPoolExecutor,
) -> bytes:
    width, height = (frame.shape[1], frame.shape[0])
    displaySize = _calculate_display_size(display)
    newSize, offset = _calculate_resize_parameters(
        sourceSize=(frame.shape[1], frame.shape[0]), maxSize=displaySize
    )

    offsetWidth, offsetHeight = offset
    newWidth, newHeight = newSize
    if width != newWidth or height != newHeight:
        frame = cv2.resize(frame, newSize, interpolation=cv2.INTER_LANCZOS4)

    base = np.full(
        shape=[displaySize[1], displaySize[0], 3],
        fill_value=0,
        dtype=frame.dtype,
    )

    y_start = offsetHeight
    y_end = offsetHeight + newHeight
    x_start = offsetWidth
    x_end = offsetWidth + newWidth
    base[y_start:y_end, x_start:x_end] = frame

    img = Image.fromarray(base)
    encoded_frame = _encode_frame(display, img, executor)
    return encoded_frame


def encode_pillow_frame(
    display: display.MonitorDisplay, img: Image.Image, executor: ThreadPoolExecutor
) -> bytes:
    displaySize = _calculate_display_size(display)
    newSize, offset = _calculate_resize_parameters(
        sourceSize=img.size, maxSize=displaySize
    )

    img = img.resize(newSize, resample=Image.Resampling.BOX)
    base = Image.new("RGB", displaySize)
    base.paste(img, offset)
    return _encode_frame(display, base, executor)


def _calculate_permonitor(display: display.MonitorDisplay) -> tuple[int, int]:
    perMonitorWidth = display.monitorWidth + L_MARGIN + R_MARGIN
    perMonitorHeight = (display.monitorHeight * 2) + T_MARGIN + B_MARGIN
    return (perMonitorWidth, perMonitorHeight)


def _calculate_display_size(display: display.MonitorDisplay) -> tuple[int, int]:
    perMonitorWidth, perMonitorHeight = _calculate_permonitor(display)
    totalWidth = perMonitorWidth * display.columns
    totalHeight = perMonitorHeight * display.rows
    return (totalWidth, totalHeight)


def _calculate_resize_parameters(
    sourceSize: tuple[int, int], maxSize: tuple[int, int]
) -> tuple[tuple[int, int], tuple[int, int]]:
    width, height = maxSize
    source_width, source_height = sourceSize

    width_ratio = width / source_width
    height_ratio = height / source_height
    scale = min(width_ratio, height_ratio)

    new_width = int(source_width * scale)
    new_height = int(source_height * scale)
    x_offset = (width - new_width) // 2
    y_offset = (height - new_height) // 2

    target_resize = (new_width, new_height)
    target_offset = (x_offset, y_offset)
    return target_resize, target_offset


def _encode_frame(
    display: display.MonitorDisplay,
    img: Image.Image,
    executor: ThreadPoolExecutor,
) -> bytes:
    per_w, per_h = _calculate_permonitor(display)

    boxes = []
    boxes_append = boxes.append

    for y in range(display.rows):
        y0 = (y * per_h) + T_MARGIN
        y1 = ((y + 1) * per_h) - B_MARGIN
        for x in range(display.columns):
            x0 = (x * per_w) - L_MARGIN
            x1 = ((x + 1) * per_w) - R_MARGIN
            boxes_append((x0, y0, x1, y1))

    monitors = (img.crop(box) for box in boxes)

    results = executor.map(
        _encode_monitor,
        ((i, monitor, display) for i, monitor in enumerate(monitors)),
    )

    return bytes([len(boxes)]) + b"".join(results)



def _encode_monitor(arg: tuple[int, Image.Image, display.MonitorDisplay]) -> bytes:
    with measure("foo"):
        index, img, display = arg

        monitor_w = display.monitorWidth
        monitor_h = display.monitorHeight

        RENDER_SIZE = monitor_w * monitor_h
        PALETTE_SIZE = 16 * 3

        writer = ByteWriter(PALETTE_SIZE + RENDER_SIZE)

        writer.writeByte(index + 1)
        writer.writeByte(monitor_w)
        writer.writeByte(monitor_h)

        img = img.quantize(colors=16)
        palette = img.palette.palette 

        palette_data = bytearray(48)
        palette_data[:48] = palette[:48]
        writer.write(palette_data)

        img_arr = np.asarray(img, dtype=np.uint8)

        height = monitor_h * 2
        width = monitor_w

        even_width = width & ~1 
        array_slice = img_arr[:height, :even_width]
        
        high = array_slice[:, 0::2]
        low = array_slice[:, 1::2]
        color_data = ((high << 4) | low).tobytes()

        color_reader = ByteReader(color_data)

        text_line = bytes([135]) * width

        for _ in range(height >> 1):
            writer.write(text_line)
            writer.write(color_reader.read(width))

        return writer.build()
