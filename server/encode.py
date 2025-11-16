import typing as t
import numpy as np
from PIL import Image, ImagePalette

from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import cv2

@dataclass
class MonitorDisplay:
    monitorWidth: int
    monitorHeight: int
    monitorRows: int
    monitorColumns: int


T_MARGIN = 2
B_MARGIN = 2
L_MARGIN = 2
R_MARGIN = 3

def calculate_permonitor(display: MonitorDisplay) -> tuple[int, int]:
    perMonitorWidth = display.monitorWidth + L_MARGIN + R_MARGIN
    perMonitorHeight = (display.monitorHeight * 2) + T_MARGIN + B_MARGIN
    return (perMonitorWidth, perMonitorHeight)

def calculate_display_size(display: MonitorDisplay) -> tuple[int, int]:
    perMonitorWidth, perMonitorHeight = calculate_permonitor(display)
    totalWidth = perMonitorWidth * display.monitorColumns
    totalHeight = perMonitorHeight * display.monitorRows
    return (totalWidth, totalHeight)


def encode_numpy_frame(
    display: MonitorDisplay,
    frame: np.ndarray,
    executor: ThreadPoolExecutor
) -> str:
    displaySize = calculate_display_size(display)
    newSize, offset = calculate_resize_parameters(
        sourceSize=(frame.shape[1], frame.shape[0]),
        maxSize=displaySize
    )

    frame = cv2.resize(
        frame,
        newSize,
        interpolation=cv2.INTER_LANCZOS4
    )
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    base = np.full(
        shape=[displaySize[1], displaySize[0], 3],
        fill_value=0,
        dtype=frame.dtype,
    )
    y_start = offset[1]
    y_end = offset[1] + newSize[1]
    x_start = offset[0]
    x_end = offset[0] + newSize[0]
    base[y_start:y_end,x_start:x_end] = frame

    img = Image.fromarray(base)
    return encode_frame(display, img, executor)


def encode_pillow_frame(
    display: MonitorDisplay,
    img: Image.Image,
    executor: ThreadPoolExecutor
) -> str:
    displaySize = calculate_display_size(display)
    newSize, offset = calculate_resize_parameters(
        sourceSize=img.size,
        maxSize=displaySize
    )

    img = img.resize(newSize, resample=Image.Resampling.BOX)
    base = Image.new("RGB", displaySize)
    base = base.paste(img, offset)
    return encode_frame(display, base, executor)


def calculate_resize_parameters(sourceSize: tuple[int, int], maxSize: tuple[int, int]) -> tuple[tuple[int, int], tuple[int, int]]:
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

def encode_frame(
    display: MonitorDisplay, img: np.ndarray, executor: ThreadPoolExecutor
) -> t.Iterable[str]:
    perMonitorWidth, perMonitorHeight = calculate_permonitor(display)

    monitors: list[Image.Image] = []
    for y in range(display.monitorRows):
        for x in range(display.monitorColumns):
            left = (x * perMonitorWidth) - L_MARGIN
            right = ((x + 1) * perMonitorWidth) - R_MARGIN
            upper = (y * perMonitorHeight) + T_MARGIN
            lower = ((y + 1) * perMonitorHeight) - B_MARGIN

            box = (left, upper, right, lower)
            monitor = img.crop(box)
            monitors.append(monitor)

    args = [
        (monitor, display)
        for monitor in monitors
    ]
    return "".join(executor.map(encode_monitor, args))


def encode_monitor(arg: tuple[int, Image.Image, MonitorDisplay]):
    img, display = arg
    output = ""

    img = img.quantize(colors=16)
    palette = img.palette
    if not palette: raise Exception("Image not quantized")
    output += _to_palette_string(palette)

    img_arr = np.array(img)

    height = display.monitorHeight * 2
    width = display.monitorWidth

    even_width = width // 2 * 2
    array_slice = img_arr[0:height, 0:even_width]

    high_nybbles = array_slice[:, 0::2]
    low_nybbles = array_slice[:, 1::2]

    byte_array = (high_nybbles.astype(np.uint8) << 4) | (low_nybbles.astype(np.uint8))
    output += byte_array.tobytes().hex().upper()

    output += "\n"
    return output


def _to_palette_string(palette: ImagePalette.ImagePalette):
    output = ""
    palette_bytes = palette.palette

    for x in range(16):
        i = x * 3
        if (i > len(palette_bytes)):
            output += "000000"
        else:
            color = int.from_bytes(palette_bytes[i : i + 3])
            output += to_hex(color, length=6)

    return output


def to_hex(value: int, *, length: int):
    return hex(value)[2:].rjust(length, "0")
