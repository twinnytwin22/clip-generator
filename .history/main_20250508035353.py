import os
from config import INPUT_DIR
from utils.transcription import transcribe_audio
from utils.clipper import cut_clips
from utils.captioner import add_captions_to_clip
from utils.metadata import generate_clip_title

def main():
    for filename in os.listdir(INPUT_DIR):
        if not filename.endswith(".mp4"):
            continue
        path = os.path.join(INPUT_DIR, filename)

        print(f"Transcribing {filename}...")
        transcript = transcribe_audio(path)

        print("Cutting clips...")
        clips = cut_clips(path, transcript)

        print("Adding captions...")
        for clip in clips:
            title = "Your caption here"
            caption_path = clip.replace(".mp4", "_captioned.mp4")
            add_captions_to_clip(clip, title, caption_path)

        print("✅ Done!")

if __name__ == "__main__":
    main()
