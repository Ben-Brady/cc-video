from pydub import AudioSegment
from pydub.audio_segment import WavData
from dataclasses import dataclass
from pydub.utils import mediainfo_json
import typing as t
import io
import struct
import audioop
import subprocess as sp
from dataclasses import dataclass

SAMPLE_RATE = 48_000

def stream_audio_from_file(filename: str, fps: float) -> t.Iterable[list[int]]:
    p = start_ffmpeg_process(filename)
    if not p.stdout:
        raise Exception("No stdout")

    return stream_audio_segments(p.stdout, fps)


def stream_audio_segments(stream: t.IO[bytes], fps: float) -> t.Iterable[list[int]]:
    wav_data = read_wav_audio(stream)

    samples_required = int(SAMPLE_RATE / fps)

    while True:
        data = wav_data.stream.read(samples_required)

        data = audioop.bias(data, 1, -128)
        view = memoryview(bytearray(data))
        yield view.cast("b").tolist()

        if len(data) != samples_required:
            break


def start_ffmpeg_process(filename: str):
    conversion_command = ["ffmpeg", '-y']
    conversion_command += ["-i", filename]
    conversion_command += ["-vn"]  # no video
    conversion_command += ["-acodec", 'pcm_u8'] # 8bit signed
    conversion_command += ["-ar", str(SAMPLE_RATE)]  # 48KHz
    conversion_command += ["-ac", "1"] # 1 channel
    conversion_command += ["-f", "wav"] # wav
    conversion_command += ["-"]

    return sp.Popen(
        conversion_command,
        stdin=None,
        stdout=sp.PIPE,
        stderr=sp.PIPE
    )


@dataclass
class WavData:
    audio_format: int
    channels: int
    sample_rate: int
    bits_per_sample: int
    stream: t.IO[bytes]


def read_wav_audio(data: t.IO[bytes]):
    headers = extract_wav_headers(data)

    fmt = [x for x in headers if x.id == b'fmt ']
    if not fmt or fmt[0].size < 16:
        raise ValueError("Couldn't find fmt header in wav data")
    fmt = fmt[0]

    audio_format = struct.unpack_from("<H", fmt.data[0:2])[0]
    if audio_format != 1 and audio_format != 0xFFFE:
        raise ValueError(f"Unknown audio format 0x{audio_format} in wav data")

    channels = struct.unpack_from("<H", fmt.data[2:4])[0]
    sample_rate = struct.unpack_from("<I", fmt.data[4:8])[0]
    bits_per_sample = struct.unpack_from("<H", fmt.data[14:16])[0]

    data_hdr = headers[-1]
    if data_hdr.id != b'data':
        raise ValueError("Couldn't find data header in wav data")

    return WavData(
        audio_format=audio_format,
        channels=channels,
        sample_rate=sample_rate,
        bits_per_sample=bits_per_sample,
        stream=data
    )


@dataclass
class WavHeader:
    id: bytes
    size: int
    data: bytes


def extract_wav_headers(data: t.IO[bytes]):
    subchunks: list[WavHeader] = []
    data.read(12)
    while len(subchunks) < 10:
        subchunk_id = data.read(4)
        subchunk_size = struct.unpack_from("<I", data.read(4))[0]
        # 'data' is the last subchunk
        if subchunk_id != b"data":
            subchunks.append(
                WavHeader(
                    id=subchunk_id,
                    size=subchunk_size,
                    data=data.read(subchunk_size)
                )
            )
        else:
            subchunks.append(WavHeader(id=subchunk_id, size=subchunk_size, data=b""))
            break

    return subchunks
