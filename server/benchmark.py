from modules import create, streams
from modules.encoder import display, MonitorDisplay
from tqdm import tqdm
import time

FILEPATH = "slop.mp4"

display = MonitorDisplay(rows=6, columns=11, monitorWidth=32, monitorHeight=24)
stream_id = create.create_file_stream(FILEPATH, display)
if not stream_id:
    raise ValueError("stream not found")

# with streams.aqquire_stream(stream_id) as stream:
#     print(len(next(stream.video)))

start = time.time()
with streams.aqquire_stream(stream_id) as stream:
    # frames = list(stream.video)
    frames = list(tqdm(stream.video, smoothing=0))

print("length:",time.time() - start)
