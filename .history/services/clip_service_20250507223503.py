# app/services/clip_service.py
import os
from config import INPUT_DIR
from utils.transcription import transcribe_audio
from utils.clipper import cut_clips
from utils.captioner import add_captions_to_clip
from utils.metadata import generate_clip_title

def process_video(filename: str):
    if not filename.endswith(".mp4"):
        raise ValueError("Only .mp4 files are supported.")

    full_path = os.path.join(INPUT_DIR, filename)
    if not os.path.isfile(full_path):
        raise FileNotFoundError(f"{filename} not found in {INPUT_DIR}")

    print(f"📄 Transcribing {filename}...")
    transcript = transcribe_audio(full_path)

    print("✂️ Cutting clips...")
    clips = cut_clips(full_path, transcript)

    print("📝 Adding captions...")
    captioned_clips = []
    for clip in clips:
        title = generate_clip_title(transcript)
        caption_path = clip.replace(".mp4", "_captioned.mp4")
        add_captions_to_clip(clip, title, caption_path)
        captioned_clips.append(caption_path)

    return captioned_clips
