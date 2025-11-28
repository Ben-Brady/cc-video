from tqdm import tqdm
from tee import tee

import video, audio, youtube

FILEPATH = "./data/heavy.mp4"

res = video.get_video_resolution(FILEPATH)
f = open(FILEPATH, "rb")
stream_1, stream_2 = tee(f)

video_frames = video.stream_video(stream_1, res, video.DISPLAY)
audio_frames = audio.stream_audio(stream_2, 20)
frames = tqdm(desc="Video", iterable=zip(video_frames, audio_frames), smoothing=0.1)
list(frames)
