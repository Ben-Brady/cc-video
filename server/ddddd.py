from pydub import AudioSegment
from pydub.audio_segment import  WavSubChunk, WavData
from dataclasses import dataclass
from pydub.utils import mediainfo_json
import typing as t
import io
import struct
import audioop
import subprocess

def stream_audio_from_file(filename: str) -> t.Iterable[AudioSegment]:
    p = start_ffmpeg_process(filename)
    p_out = bytearray(p.stdout.read())
    wav_data = read_wav_audio(p_out)

    segment = object.__new__(AudioSegment)
    if not wav_data:
        raise ValueError("Couldn't read wav audio from data")

    segment.channels = wav_data.channels
    segment.sample_width = wav_data.bits_per_sample // 8
    segment.frame_rate = wav_data.sample_rate
    segment.frame_width = segment.channels * segment.sample_width
    segment._data = wav_data.stream.read()

    if segment.sample_width == 1:
        # convert from unsigned integers in wav
        segment._data = audioop.bias(segment._data, 1, -128)

    yield segment


def start_ffmpeg_process(filename: str):
    conversion_command = ["ffmpeg", '-y']
    READ_AHEAD_LIMIT = READ_AHEAD_LIMIT = -1

    conversion_command += ["-i", filename]
    stdin_parameter = None

    info = mediainfo_json(filename, read_ahead_limit=READ_AHEAD_LIMIT)
    if info:
        audio_streams = [
            x for x in info['streams']
            if x['codec_type'] == 'audio'
        ]

        # This is a workaround for some ffprobe versions that always say
        # that mp3/mp4/aac/webm/ogg files contain fltp samples
        audio_codec = audio_streams[0].get('codec_name')
        if (audio_streams[0].get('sample_fmt') == 'fltp' and
                audio_codec in ['mp3', 'mp4', 'aac', 'webm', 'ogg']):
            bits_per_sample = 16
        else:
            bits_per_sample = audio_streams[0]['bits_per_sample']

        if bits_per_sample == 8:
            acodec = 'pcm_u8'
        else:
            acodec = 'pcm_s%dle' % bits_per_sample

        conversion_command += ["-acodec", acodec]

    conversion_command += [
        "-vn",  # Drop any video streams if there are any
        "-f", "wav"  # output options (filename last)
    ]

    conversion_command += ["-"]

    return subprocess.Popen(
        conversion_command,
        stdin=stdin_parameter,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def fix_wav_headers(data: bytes):
    headers = extract_wav_headers(data)
    if not headers or headers[-1].id != b'data':
        return

    # Set the data size in the data subchunk
    pos = headers[-1].position
    data[pos + 4:pos + 8] = struct.pack('<I', len(data) - pos - 8)



def extract_wav_headers(data: bytes):
    # def search_subchunk(data, subchunk_id):
    pos = 12  # The size of the RIFF chunk descriptor
    subchunks = []
    while pos + 8 <= len(data) and len(subchunks) < 10:
        subchunk_id = data[pos:pos + 4]
        subchunk_size = struct.unpack_from('<I', data[pos + 4:pos + 8])[0]
        subchunks.append(WavSubChunk(subchunk_id, pos, subchunk_size))
        if subchunk_id == b'data':
            # 'data' is the last subchunk
            break
        pos += subchunk_size + 8

    return subchunks

@dataclass
class WavData:
    audio_format: str
    channels: int
    sample_rate: int
    bits_per_sample: int
    stream: io.BytesIO


def read_wav_audio(data: bytearray):
    fix_wav_headers(data)
    headers = extract_wav_headers(data)

    fmt = [x for x in headers if x.id == b'fmt ']
    if not fmt or fmt[0].size < 16:
        raise ValueError("Couldn't find fmt header in wav data")
    fmt = fmt[0]
    pos = fmt.position + 8
    audio_format = struct.unpack_from('<H', data[pos:pos + 2])[0]
    if audio_format != 1 and audio_format != 0xFFFE:
        raise ValueError(f"Unknown audio format 0x{audio_format} in wav data")

    channels = struct.unpack_from('<H', data[pos + 2:pos + 4])[0]
    sample_rate = struct.unpack_from('<I', data[pos + 4:pos + 8])[0]
    bits_per_sample = struct.unpack_from('<H', data[pos + 14:pos + 16])[0]

    data_hdr = headers[-1]
    if data_hdr.id != b'data':
        raise ValueError("Couldn't find data header in wav data")

    pos = data_hdr.position + 8
    return WavData(
        audio_format=audio_format,
        channels=channels,
        sample_rate=sample_rate,
        bits_per_sample=bits_per_sample,
        stream=io.BytesIO(data[pos:pos + data_hdr.size])
    )
