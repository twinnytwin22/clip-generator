import subprocess
#import os

def enhance_audio(input_video_path: str, output_audio_path: str) -> str:
    """
    Extract and enhance audio from a video using FFmpeg filters.
    Returns the path to the enhanced audio file.
    """
    cmd = [
        "ffmpeg", "-y", "-i", input_video_path,
        "-af", "highpass=f=200, lowpass=f=3000, dynaudnorm",  # noise cleanup + normalize
        "-ac", "1",  # mono
        "-ar", "16000",  # resample to 16kHz
        "-vn",  # no video
        output_audio_path
    ]
    subprocess.run(cmd, check=True)
    return output_audio_path
