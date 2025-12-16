# CC Video

https://github.com/user-attachments/assets/807abc87-74a7-4ce4-9277-b2a55591de48


**Features:**

- Video Encoding
    - 320p resolution
    - 16 bit colour quantised blocks
- u8_pcm audio encoding
    - Properly mastered to ensure max quality
- Full colour support
- Youtube streaming
- Buffering Support

This project has been really fun for me, it started with the idea of pushing computer craft's displays to their limits and has ended up as a full youtube stream encoder pipeline.
I learned a lot about stdout/in, pipes, and ffmpeg.
 
Monitors in computer craft are limited to 16 colours, but I had the idea to try and get around the limitation by breaking it down into multiple displays.

This was my first verison in 2023:

https://github.com/user-attachments/assets/8caa0785-d2f1-46c9-b26d-4aea268b2a70

A few months ago, I wanted to see if I could do it better with a much simpler encoder and decoder.

In about a day, I had a version re-made from scratch that was around 200 lines total, and performed way better:

https://github.com/user-attachments/assets/a2b70f1d-a5f2-44db-82f5-c981f12397a9

Over the course of the next few weeks, I toiled away improving it and adding features such as audio playback, improving the resolution and quantisation, swapping to 2x2 monitors.

I eventually reworked my entire video and audio encoder pipeline into two different ffmpeg commands using a raw output, meaning I could also do processing with it.

```
# video
ffmpeg -i - -vf scale=854:480,fps=fps=20 -f rawvideo -pix_fmt rgb24 -

# audio
ffmpeg -i - -vn -ar 48000 -ac 1 -f s8 -y -

# audio (with filters)
ffmpeg -i - -vn -ar 48000 -ac 1 -filter:a lowpass=f=18000,compand=attacks=0.3:decays=0.8:soft-knee=1.2:points=-90/-100|-50/-80|-45/-15|-20/-12|-4/-4|0/0,loudnorm=I=-8:LRA=7:tp=-0.1 -f s8 -y -
```

Along with some other optimisations, this meant I had enough performance to encode video faster than playback, which meant I could stream video.

Steaming support meant I could support very long videos or live streams, since I didn't have to worry about storing everything in memory.
Honestly the hardest part in doing this was figuring out how to tee stdout in python, I eventually figured out how using pipes and a queue, but it's suprisingly hard.

I hooked it up to yt-dlp, and now I have working youtube video streaming:

https://github.com/user-attachments/assets/c162873e-26d3-472e-a3d6-8f54d4cb4d7e

This project is probably over for now, I've tidied it up the best I can and there may be some minor improvements I can do.
But it's way better than I expected already, and I've learned so much from it, I'm very glad to have done it.

The one thing left to do is setup input streaming and hook it up to doom :)
