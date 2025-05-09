import os
from faster_whisper import WhisperModel
from moviepy.video.io.VideoFileClip import VideoFileClip

def transcribe_audio(video_path: str, start_time: float = None, end_time: float = None) -> list:
    """
    Transcribe audio from a specific portion of a video file using Fast Whisper.

    Args:
        video_path (str): Path to the video file.
        start_time (float): Start time of the segment to transcribe (in seconds).
        end_time (float): End time of the segment to transcribe (in seconds).

    Returns:
        list: List of transcript segments with 'start', 'end', and 'text'.
    """
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # If start_time and end_time are provided, extract the clip
    if start_time is not None and end_time is not None:
        with VideoFileClip(video_path) as video:
            clip_path = "temp_clip.mp4"
            video.subclip(start_time, end_time).write_videofile(clip_path, codec="libx264")
            video_path = clip_path

    # Load the Fast Whisper model
    model = WhisperModel("base", device="cpu")  # Use "cuda" for GPU acceleration if available

    # Transcribe the video
    segments, _ = model.transcribe(video_path)

    # Convert segments to a list of dictionaries
    transcript = []
    for segment in segments:
        transcript.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text
        })

    # Clean up temporary clip if created
    if start_time is not None and end_time is not None:
        os.remove(clip_path)

    return transcript