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
    args = ["yt-dlp"]
    args += [url]
    args += ["--js-runtimes", "node"]
    args += ["--no-playlist"]
    args += ["--quiet"]
    args += ["-f", "bestvideo[height=480]+bestaudio"]
    args += ["-o", "-"]
    print(" ".join(args))
    p = sp.Popen(args, stdout=sp.PIPE)
    atexit.register(lambda: p.kill())

    # TODO Don't do fixed res, learn how to retrive res
    res = 854, 480
    return YoutubeStream(
        resolution=res,
        stream=t.cast(t.IO[bytes], p.stdout),
        process=p
    )
