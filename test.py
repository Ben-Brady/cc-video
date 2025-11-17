import subprocess as sp
from namedpipe import NPopen


pipes: list[NPopen] = []

video_pipe = NPopen('r')
args = [
    "yt-dlp",
    "-f",
    "best[height<=480]",
    "https://youtu.be/hxOOAjHl-X0",
    "-o",
    video_pipe.path,
]
p_ytdlp = sp.Popen(args)


args = [
    "ffmpeg",
    "-hide_banner",
    "-y",
    "-i",
    video_pipe.path,
    "-acodec",
    "pcm_u8",
    "-vn",
    "-f",
    "wav",
    "test.wav",
]
p_ffmpeg = sp.Popen(args)
p_ffmpeg.communicate()
