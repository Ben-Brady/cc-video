import typing as t
from dataclasses import dataclass
import subprocess as sp
import atexit


@dataclass
class YoutubeStream:
    resolution: tuple[int, int]
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
    print(" ".join(cmd))

    p = sp.Popen(cmd, stdout=sp.PIPE)
    atexit.register(lambda: p.kill())

    # TODO Don't do fixed res, learn how to retrive res
    res = 854, 480
    return YoutubeStream(
        resolution=res, stream=t.cast(t.IO[bytes], p.stdout), process=p
    )
