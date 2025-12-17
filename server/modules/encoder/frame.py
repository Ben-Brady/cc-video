import numpy as np
from PIL import Image
from concurrent.futures import ThreadPoolExecutor
import cv2
from . import display
from .bytes import ByteWriter

T_MARGIN = 0
B_MARGIN = 0
L_MARGIN = 0
R_MARGIN = 0
# T_MARGIN = 3
# B_MARGIN = 4
# L_MARGIN = 3
# R_MARGIN = 3


def encode_frame(
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

    base = np.zeros((displaySize[1], displaySize[0], 3), dtype=np.uint8)

    y_start = offsetHeight
    y_end = offsetHeight + newHeight
    x_start = offsetWidth
    x_end = offsetWidth + newWidth
    base[y_start:y_end, x_start:x_end] = frame

    img = Image.fromarray(base)
    encoded_frame = _encode_processed_frame(display, img, executor)
    return encoded_frame


def _encode_processed_frame(
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
        _encode_monitor,
        [(i, monitor, display) for i, monitor in enumerate(monitors)],
    )
    frame_data = b"".join(results)

    return monitor_count_byte + frame_data


def _encode_monitor(arg: tuple[int, Image.Image, display.MonitorDisplay]) -> bytes:
    global hits, nonhits
    index, img, display = arg
    width, height = img.width, img.height

    PALETTE_SIZE = 3 * 16
    RENDER_SIZE = display.monitorWidth * display.monitorHeight
    writer = ByteWriter(PALETTE_SIZE + RENDER_SIZE)

    writer.writeByte(index + 1)
    writer.writeByte(display.monitorWidth)
    writer.writeByte(display.monitorHeight)

    img = img.quantize(colors=16, method=Image.Quantize.MEDIANCUT)
    assert img.palette, "Image not quantized"
    palette = img.palette.palette

    palette_data = bytearray(48)
    palette_data[0 : len(palette)] = palette[:48]
    writer.write(palette_data)

    height = display.monitorHeight * 2
    width = display.monitorWidth

    # combine 4 bit values into bytes
    pixels = np.array(img).flatten()
    high_nibbles = pixels[0::2]
    low_nibbles = pixels[1::2]
    color_data = (low_nibbles | (high_nibbles << 4)).tobytes()

    text_data = bytes([135]) * width

    writer_array = writer.array
    writer_cursor = writer.cursor

    for x in range(height // 2):
        writer_array[writer_cursor : writer_cursor + width] = text_data
        writer_cursor += width

        start = x * width
        data = color_data[start : start + width]

        writer_array[writer_cursor : writer_cursor + width] = data
        writer_cursor += width

    writer.cursor = writer_cursor
    return writer.build()


def _calculate_permonitor(display: display.MonitorDisplay) -> tuple[int, int]:
    perMonitorWidth = display.monitorWidth + L_MARGIN + R_MARGIN
    perMonitorHeight = (display.monitorHeight * 2) + T_MARGIN + B_MARGIN
    return (perMonitorWidth, perMonitorHeight)


def _calculate_display_size(display: display.MonitorDisplay) -> tuple[int, int]:
    perMonitorWidth, perMonitorHeight = _calculate_permonitor(display)
    totalWidth = perMonitorWidth * display.columns
    totalHeight = perMonitorHeight * display.rows
    return (totalWidth, totalHeight)


def caclulate_target_res(
    res: tuple[int, int], display: display.MonitorDisplay
) -> tuple[int, int]:
    displaySize = _calculate_display_size(display)
    newSize, _ = _calculate_resize_parameters(sourceSize=res, maxSize=displaySize)
    return newSize


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
