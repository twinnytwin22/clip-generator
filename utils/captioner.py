from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

def add_captions_to_clip(clip_path, caption_text, output_path):
    """
    Add captions to a video clip.

    Args:
        clip_path (str): Path to the video clip.
        caption_text (str): Text to overlay as captions.
        output_path (str): Path to save the captioned video.
    """
    video = VideoFileClip(clip_path)

    # Create the text clip
    txt_clip = TextClip(
        caption_text,
        fontsize=48,
        color="white",
        font="Arial",  # Ensure this font is available on your system
        method="caption",
        size=video.size
    ).set_position(("center", "bottom")).set_duration(video.duration)

    # Overlay the text clip on the video
    final = CompositeVideoClip([video, txt_clip])
    final.write_videofile(output_path, codec="libx264")
    print(f"Adding captions to {clip_path}. Output: {output_path}")