import typing as t
from dataclasses import dataclass
import subprocess as sp
import atexit


@dataclass
class YoutubeStream:
    stream: t.IO[bytes]
    close: t.Callable[[]]


def get_youtube_stream(id: str) -> YoutubeStream | None:
    cmd = ["yt-dlp"]
    cmd += [f"https://www.youtube.com/watch?v={id}"]
    cmd += ["--js-runtimes", "node"]
    cmd += ["--no-playlist"]
    cmd += ["--quiet"]
    cmd += ["-f", "bestvideo[height=480]+bestaudio"]
    cmd += ["-o", "-"]

    p = sp.Popen(cmd, stdout=sp.PIPE)
    atexit.register(lambda: p.kill())
    stream = t.cast(t.IO[bytes], p.stdout)

    return YoutubeStream(stream=stream, close=lambda: p.kill())
