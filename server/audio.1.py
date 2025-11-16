import soundfile as sf
import time
import numpy as np
from pydub import AudioSegment
from pydub.audio_segment import fix_wav_headers, WavSubChunk, WavData
from pydub.effects import normalize
import typing as t
from ddddd import stream_audio_from_file
import io
import struct

AudioChunk: t.TypeAlias = t.Sequence[int]

T = t.TypeVar("T")
CHUNK_SIZE = 1024 * 128
SAMPLE_RATE = 48_000


def stream_video_file(filepath: str, fps: float) -> t.Iterable[AudioChunk]:
    segments = stream_audio_from_file(filepath)
    frame_samples = int(SAMPLE_RATE // fps)

    for segment in segments:
        segment: AudioSegment = segment
        segment = segment.set_frame_rate(SAMPLE_RATE).set_channels(1).set_sample_width(1)
        segment = normalize(segment)
        data = np.array(list(segment._data))
        data = (data.astype(np.int16) - 127).astype(np.int8)
        offset = 0

        while len(data) > offset:
            print(set(data[offset : offset + frame_samples]))
            yield data[offset: offset + frame_samples].tolist()
            offset += frame_samples
