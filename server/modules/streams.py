import typing as t
from dataclasses import dataclass
from random import randint
from contextlib import contextmanager
import atexit
from modules import monitor

streams: dict[str, Stream] = {}


@dataclass
class Stream:
    display: monitor.MonitorDisplay
    video: t.Generator[str]
    audio: t.Generator[str] | None = None
    onclose: t.Callable[[], None] | None = None
    counter = 0


def create_stream(
    display: monitor.MonitorDisplay,
    video: t.Generator[str],
    audio: t.Generator[str] | None = None,
    onclose: t.Callable[[], None] | None = None,
):
    stream = Stream(
        display=display,
        video=video,
        audio=audio,
        onclose=onclose,
    )
    stream_id = str(randint(0, 2**16))
    streams[stream_id] = stream
    atexit.register(lambda: close_stream(stream_id))

    return stream_id


def close_stream(id: str):
    stream = streams.get(id)
    if not stream:
        return

    if stream.onclose:
        stream.onclose()

    del streams[id]


@contextmanager
def aqquire_stream(id: str):
    if id not in streams:
        print(f"Stream '{id}' not found")
        raise KeyError(f"Can't find stream")

    stream = streams[id]
    stream.counter += 1

    try:
        yield stream
    finally:
        stream.counter -= 1

        if stream.counter <= 0:
            close_stream(id)
