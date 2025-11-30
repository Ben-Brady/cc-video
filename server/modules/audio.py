import io
import json
import typing as t
import subprocess as sp


AudioChunk: t.TypeAlias = t.Sequence[float]

SAMPLE_RATE = 48_000
FRAMERATE = 20


def stream_audio_from_file(filepath: str) -> t.Generator[str]:
    with open(filepath, "rb") as f:
        yield from stream_audio(f)


def stream_audio(stream: t.IO[bytes]) -> t.Generator[str]:
    filters = []
    filters += ["lowpass=f=18000"]
    filters += [
        "compand=attacks=0.3:decays=0.8:soft-knee=1.2:points=-90/-100|-50/-80|-45/-15|-20/-12|-4/-4|0/0"
    ]
    filters += ["loudnorm=I=-8:LRA=7:tp=-0.1"]

    cmd = ["ffmpeg"]
    cmd += ["-i", "-"]
    cmd += ["-vn"]  # no video
    cmd += ["-ar", "48000"]  # 48KHz
    cmd += ["-ac", "1"]  # 1 channel
    cmd += ["-filter:a", ",".join(filters)]  # audio normalisation
    cmd += ["-f", "s8"]  # 1 byte
    cmd += ["-y"]  # overwrite output
    cmd += ["-"]

    print(" ".join(cmd))
    p = sp.Popen(
        cmd,
        stdin=stream,
        stdout=sp.PIPE,
        stderr=sp.DEVNULL,
    )

    stdout = t.cast(io.BytesIO, p.stdout)
    size = int(SAMPLE_RATE / FRAMERATE)
    while True:
        data = stdout.read(size)
        view = memoryview(bytearray(data))
        samples = view.cast("b").tolist()
        data = json.dumps(samples)
        yield data

        if len(data) < size:
            return
