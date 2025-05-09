import os
from config import OUTPUT_DIR
from moviepy.video.io.VideoFileClip import VideoFileClip

def cut_clips(filepath, transcript, min_words=20, max_clips=1):
    """
    Cut the video into clips based on the transcript.

    Args:
        filepath (str): Path to the video file.
        transcript (list): List of transcript segments with 'start', 'end', and 'text'.
        min_words (int): Minimum number of words required in a segment to create a clip.
        max_clips (int): Maximum number of clips to create (optional).

    Returns:
        list: List of file paths to the created clips.
    """
    clips = []
    video = VideoFileClip(filepath)

    for i, seg in enumerate(transcript):
        if len(seg["text"].split()) < min_words:
            continue

        if max_clips is not None and len(clips) >= max_clips:
            break  # Stop if the maximum number of clips is reached

        start = seg["start"]
        end = seg["end"]
        clip = video.subclip(start, end)
        out_path = os.path.join(OUTPUT_DIR, f"clip_{i}.mp4")
        clip.write_videofile(out_path, codec="libx264")
        clips.append(out_path)

    return clips