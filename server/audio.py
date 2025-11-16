import soundfile as sf
import time
from concurrent.futures import ThreadPoolExecutor
from pydub import AudioSegment
from pydub.audio_segment import fix_wav_headers, WavSubChunk
from pydub.effects import normalize
from pydub.utils import mediainfo_json
import typing as t
import numpy as np
from itertools import batched

AudioChunk: t.TypeAlias = t.Sequence[t.Sequence[float]]
AudioStream: t.TypeAlias = t.Sequence[AudioChunk]

T = t.TypeVar("T")
CHUNK_SIZE = 1024 * 128
SAMPLE_RATE = 48_000


def stream_video_file(filepath: str, fps: float) -> t.Iterable[AudioChunk]:
    start = time.time()
    stream = encode_audio_file(filepath)
    duration = time.time() - start
    print(f"Audio Encoding: {duration * 1000:.2f}ms")
    stream = list(stream)
    frame_samples = int(SAMPLE_RATE // fps)

    offset = 0
    while len(stream) > offset:
        yield stream[offset: offset + frame_samples]
        offset += frame_samples


def encode_audio_file(filepath: str) -> list[int]:
    audio: AudioSegment = AudioSegment.from_file(filepath)
    audio = audio.set_frame_rate(SAMPLE_RATE).set_channels(1).set_sample_width(1)
    audio = normalize(audio)
    return list(audio.get_array_of_samples())
