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

    conversion_command = ["ffmpeg"]
    conversion_command += ["-i", "-"]
    conversion_command += ["-vn"]  # no video
    conversion_command += ["-ar", "48000"]  # 48KHz
    conversion_command += ["-ac", "1"]  # 1 channel
    conversion_command += ["-filter:a", ",".join(filters)]  # audio normalisation
    conversion_command += ["-f", "s8"]  # 1 byte
    conversion_command += ["-y"]  # overwrite output
    conversion_command += ["-"]

    print(" ".join(conversion_command))
    p = sp.Popen(
        conversion_command,
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
