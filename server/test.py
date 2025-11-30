from tqdm import tqdm
from modules import video, audio, tee, monitor, create, streams

FILEPATH = "./data/heavy.mp4"

display = monitor.MonitorDisplay(rows=5, columns=11, monitorHeight=36, monitorWidth=24)
stream_id = create.create_youtube_stream("YlLn5DXTRxI", display)
if not stream_id:
    raise ValueError("Youtube vivode not found")

with streams.aqquire_stream(stream_id) as stream:
    iterable = zip(stream.video, stream.audio)
    frames = tqdm(desc="Video", iterable=iterable, smoothing=0.1)
    list(frames)
