from pydub import AudioSegment
from pydub.effects import normalize
from pydub_utils import stream_audio_from_file
import typing as t
import audioop

AudioChunk: t.TypeAlias = t.Sequence[float]

CHUNK_SIZE = 1024 * 128
SAMPLE_RATE = 48_000


def stream_video_file(filepath: str, fps: float) -> t.Iterable[AudioChunk]:
    yield from stream_audio_from_file(filepath, fps)

# def stream_video_file(filepath: str, fps: float) -> t.Iterable[AudioChunk]:
#     data = encode_audio_file(filepath)
#     samples = SAMPLE_RATE // fps

#     offset = 0
#     while offset < len(data):
#         yield data[offset: offset + samples]
#         offset += samples

def encode_audio_file(filepath: str) -> list[int]:
    audio: AudioSegment = AudioSegment.from_file(filepath)
    audio = audio.set_frame_rate(SAMPLE_RATE).set_channels(1).set_sample_width(1)
    return list(audio.get_array_of_samples())
