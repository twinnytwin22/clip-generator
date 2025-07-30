from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

def add_captions_to_clip(input_path, transcript, output_path, font="Arial-Bold", fontsize=48, color="white", bg_color="black"):
    """
    Add word-by-word or line-by-line captions to a video clip based on transcript with timing.

    Args:
        input_path (str): Path to input video.
        transcript (list): List of dicts with 'start', 'end', and 'text'.
        output_path (str): Path to save captioned video.
        font (str): Font to use for captions.
        fontsize (int): Font size for captions.
        color (str): Font color for captions.
        bg_color (str): Background color for captions.

    Returns:
        None
    """
    video = VideoFileClip(input_path)
    caption_clips = []

    for word in transcript:
        start = float(word["start"])
        end = float(word["end"])
        text = word["text"]

        # Create a TextClip for each word or line
        txt_clip = (TextClip(text, fontsize=fontsize, font=font, color=color, bg_color=bg_color, method="caption")
                    .set_position(("center", "bottom"))
                    .set_start(start)
                    .set_end(end))
        caption_clips.append(txt_clip)

    # Combine the video with the caption clips
    final = CompositeVideoClip([video, *caption_clips])
    final.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=video.fps)