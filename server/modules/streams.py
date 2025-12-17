from __future__ import annotations
import typing as t
import itertools
from dataclasses import dataclass
from random import randint
from contextlib import contextmanager
import atexit
from modules.encoder import MonitorDisplay

streams: dict[str, Stream] = {}


@dataclass
class Stream:
    id: str
    display: MonitorDisplay
    video: t.Iterator[bytes]
    audio: t.Iterator[bytes] | None = None
    onclose: t.Callable[[], None] | None = None
    counter = 0


def create_stream(
    display: MonitorDisplay,
    video: t.Iterator[bytes],
    audio: t.Iterator[bytes] | None = None,
    onclose: t.Callable[[], None] | None = None,
):
    stream_id = str(randint(0, 2**16))
    stream = Stream(
        id=stream_id,
        display=display,
        video=ensure_stream_started(video),
        audio=ensure_stream_started(audio) if audio else None,
        onclose=onclose,
    )
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
        raise KeyError(f"Stream '{id}' not found")

    stream = streams[id]
    stream.counter += 1

    try:
        yield stream
    finally:
        stream.counter -= 1

        if stream.counter <= 0:
            close_stream(id)


def ensure_stream_started[T](iterable: t.Iterator[T]) -> t.Iterator[T]:
    try:
        first = next(iterable)
        return itertools.chain([first], iterable)
    except StopIteration:
        return iter([])
