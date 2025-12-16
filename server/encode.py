from modules import create, streams
from modules.encoder import display
from modules.encoder.bytes import ByteReader
from tqdm import tqdm
from PIL import Image
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import cv2

FILEPATH = "slop.mp4"

display = display.MonitorDisplay(rows=3, columns=7, monitorWidth=32, monitorHeight=24)
stream_id = create.create_file_stream(FILEPATH, display)
if not stream_id:
    raise ValueError("stream not found")

with streams.aqquire_stream(stream_id) as stream:
    output = []
    for i, frame in tqdm(enumerate(stream.video)):
        reader = ByteReader(frame)
        length = reader.read(1)[0]

        img = Image.new(
            "RGB",
            (
                display.columns * display.monitorWidth,
                display.rows * display.monitorHeight * 2,
            ),
        )

        for i in range(length):
            index = reader.readByte() - 1
            width = reader.readByte()
            height = reader.readByte()

            monitor = Image.new("P", (width, height * 2))

            colors = []
            for x in range(16):
                r = reader.readByte()
                g = reader.readByte()
                b = reader.readByte()
                colors.extend([r, g, b])

            monitor.putpalette(colors, "RGB")
            for y in range(height):
                text = reader.read(width)
                color = reader.read(width)

                blit = color.hex()
                bgBlit = blit[:width]
                fgBlit = blit[width:]

                for x in range(width):
                    bg = int(bgBlit[x], 16)
                    fg = int(fgBlit[x], 16)
                    monitor.putpixel((x, y * 2), bg)
                    monitor.putpixel((x, (y * 2) + 1), fg)

            frame = np.array(monitor.convert("RGB"))

            x = i % display.columns
            y = i // display.columns
            x_offset = x * monitor.width
            y_offset = y * monitor.height
            img.paste(monitor, (x_offset, y_offset))

        cv2.imshow("Frame", cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR))
        cv2.waitKey(1)
        output.append(img)

    output[0].save(
        "pillow_imagedraw.gif",
        save_all=True,
        append_images=output[1:],
        optimize=False,
        duration=50,
    )
