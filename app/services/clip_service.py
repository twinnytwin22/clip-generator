import requests
import os
from config import INPUT_DIR
from utils.transcription import transcribe_audio
from utils.clipper import cut_clips
from utils.captioner import add_captions_to_clip
from utils.metadata import generate_clip_metadata

def download_file(url: str, output_dir: str) -> str:
    """
    Download a file from a URL and save it locally.
    """
    local_filename = os.path.join(output_dir, os.path.basename(url))
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return local_filename

def process_video(filename: str, min_words=20, max_clips=5):
    """
    Process a video file to generate clips with captions.

    Args:
        filename (str): Path to the video file or URL.
        min_words (int): Minimum number of words required in a segment to create a clip.
        max_clips (int): Maximum number of clips to create.

    Returns:
        list: List of file paths to the captioned clips.
    """
    # Handle remote URLs
    if filename.startswith("http"):
        filename = download_file(filename, INPUT_DIR)

    if not filename.endswith(".mp4"):
        raise ValueError("Only .mp4 files are supported.")

    full_path = os.path.join(INPUT_DIR, filename)
    if not os.path.isfile(full_path):
        raise FileNotFoundError(f"{filename} not found in {INPUT_DIR}")

    # Cut clips based on predefined criteria
    print("✂️ Cutting clips...")
    transcript = transcribe_audio(full_path)  # Transcribe the entire video to identify segments
    clips = cut_clips(full_path, transcript, min_words=min_words, max_clips=max_clips)
    if not clips:
        raise ValueError("No clips generated. Please check the video file or criteria.")
    print(f"✅ Clips created: {clips}")

    # Transcribe each clip and generate captions
    captioned_clips = []
    for clip in clips:
        print(f"📄 Transcribing clip: {clip}")
        clip_transcript = transcribe_audio(clip)  # Transcribe only the clip
        if not clip_transcript:
            print(f"⚠️ No transcript generated for clip: {clip}")
            continue

        # Combine transcript text for OpenAI
        clip_text = " ".join([seg["text"] for seg in clip_transcript])
        print(f"📝 Generating metadata for clip: {clip}")
        metadata = generate_clip_metadata(clip_text)  # Generate title and hashtags

        # Add captions to the clip
        title = metadata.get("title", "Untitled Clip")
        caption_path = clip.replace(".mp4", "_captioned.mp4")
        print(f"🎥 Adding captions to clip: {clip}")
        add_captions_to_clip(clip, title, caption_path)
        captioned_clips.append(caption_path)

    return captioned_clips