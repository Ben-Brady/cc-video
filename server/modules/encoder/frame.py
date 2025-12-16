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
    display: display.MonitorDisplay, img: Image.Image, executor: ThreadPoolExecutor
) -> bytes:
    perMonitorWidth, perMonitorHeight = _calculate_permonitor(display)

    monitors: list[Image.Image] = []
    for y in range(display.rows):
        for x in range(display.columns):
            left = (x * perMonitorWidth) - L_MARGIN
            right = ((x + 1) * perMonitorWidth) - R_MARGIN
            upper = (y * perMonitorHeight) + T_MARGIN
            lower = ((y + 1) * perMonitorHeight) - B_MARGIN

            box = (left, upper, right, lower)
            monitor = img.crop(box)
            monitors.append(monitor)

    monitor_count_byte = bytes([len(monitors)])

    results = executor.map(
        _encode_monitor, [(i, monitor, display) for i, monitor in enumerate(monitors)]
    )
    frame_data = b"".join(results)

    return monitor_count_byte + frame_data


def _encode_monitor(arg: tuple[int, Image.Image, display.MonitorDisplay]) -> bytes:
    with measure("foo"):
        index, img, display = arg

        RENDER_SIZE = display.monitorWidth * display.monitorHeight
        PALETTE_SIZE = 16 * 3
        writer = ByteWriter(PALETTE_SIZE + RENDER_SIZE)

        writer.writeByte(index + 1)
        writer.writeByte(display.monitorWidth)
        writer.writeByte(display.monitorHeight)

        img = img.quantize(colors=16)
        assert img.palette, "Image not quantized"
        palette = img.palette.palette

        palette_data = bytearray(48)
        palette_data[0 : len(palette)] = palette[:48]

        writer.write(palette_data)

        img_arr = np.array(img)

        height = display.monitorHeight * 2
        width = display.monitorWidth

        even_width = width // 2 * 2
        array_slice = img_arr[0:height, 0:even_width]

        # combine 4 bit values into bytes
        high_nibbles = array_slice[:, 0::2].astype(np.uint8)
        low_nibbles = array_slice[:, 1::2].astype(np.uint8)
        color_data = ((high_nibbles << 4) | (low_nibbles)).tobytes()

        color_reader = ByteReader(color_data)

        for _ in range(height // 2):
            text_data = bytes([135 for _ in range(width)])
            writer.write(text_data)
            line_color = color_reader.read(width)
            writer.write(line_color)

        return writer.build()
