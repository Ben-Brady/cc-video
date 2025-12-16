import typing as t
from dataclasses import dataclass
import subprocess as sp
import atexit


@dataclass
class YoutubeStream:
    stream: t.IO[bytes]
    process: sp.Popen[bytes]


def get_youtube_stream(url: str) -> YoutubeStream | None:
    cmd = ["yt-dlp"]
    cmd += [url]
    cmd += ["--js-runtimes", "node"]
    cmd += ["--no-playlist"]
    cmd += ["--quiet"]
    cmd += ["-f", "bestvideo[height=480]+bestaudio"]
    cmd += ["-o", "-"]
    # print(" ".join(cmd))

    p = sp.Popen(cmd, stdout=sp.PIPE)
    atexit.register(lambda: p.kill())

    return YoutubeStream(stream=t.cast(t.IO[bytes], p.stdout), process=p)
