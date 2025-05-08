import moviepy.editor as mp
import os
from config import OUTPUT_DIR

def cut_clips(filepath, transcript, min_words=5):
    clips = []
    video = mp.VideoFileClip(filepath)

    for i, seg in enumerate(transcript):
        if len(seg["text"].split()) < min_words:
            continue

        start = seg["start"]
        end = seg["end"]
        clip = video.subclip(start, end)
        out_path = os.path.join(OUTPUT_DIR, f"clip_{i}.mp4")
        clip.write_videofile(out_path, codec="libx264")
        clips.append(out_path)

    return clips
