import requests
import os
from clip_generator.config import INPUT_DIR
from clip_generator.utils.transcription import transcribe_audio
from clip_generator.utils.clipper import cut_clips
from clip_generator.utils.supabaseClient.supabase import supabase

max_clips = 3


def download_file(path_in_bucket: str, profile_id: str, output_dir: str) -> str:
    """
    Download a file from Supabase Storage using a signed URL if profile_id is provided,
    otherwise treat it as a public URL.

    Args:
        path_in_bucket (str): The path of the file in the 'uploads' bucket.
        profile_id (str): The profile ID; used to determine whether to sign the URL.
        output_dir (str): The local directory to save the downloaded file.

    Returns:
        str: The local file path of the downloaded file.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    filename = os.path.basename(path_in_bucket)
    local_path = os.path.join(output_dir, filename)

    # Get a signed URL if profile_id is provided (indicating a private file)
    if profile_id:
        print(f"🔐 Generating signed URL for: {path_in_bucket}")
        result = supabase.storage.from_("uploads").create_signed_url(path_in_bucket, 3600)
        print(f"🔐 Signed URL: {result}")
        # if not signed_url or "token=" not in signed_url:
        #     raise ValueError("Invalid signed URL returned from Supabase.")

        url_to_download = result.get("signedURL")
    else:
        # If public access, construct public URL
        # Change `your-project-id` as needed
        raise ValueError("Public URL access is not supported in this context.")

    print(f"⬇️ Downloading: {url_to_download}")
    with requests.get(url_to_download, stream=True) as r:
        r.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"✅ File saved: {local_path}")
    return local_path



def process_video(filename: str, project_id: str, profile_id: str, min_words=5, max_clips=max_clips):
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
    if filename:
        print("downloading file...")
        filename = download_file(filename,profile_id,INPUT_DIR)


    if not filename:
        raise ValueError("You need files")

    full_path = os.path.join(INPUT_DIR, filename)
    if not os.path.isfile(full_path):
        raise FileNotFoundError(f"{filename} not found in {INPUT_DIR}")

    # Transcribe the entire video to identify segments
    print(" transcribing video...")
    audio = transcribe_audio(full_path, project_id, profile_id, chunk_size=5.0)

    projectTranscript = audio.get("transcript")
    if not projectTranscript:
        raise ValueError("No transcript generated. Please check the video file.")

    print("✂️ Cutting clips...")
    clips = cut_clips(full_path, projectTranscript, project_id, min_words=min_words, max_clips=max_clips)
    if not clips.get('status') == "ready":
        raise ValueError("No clips generated. Please check the video file or criteria.")
    print(f"✅ Clips created: {clips}")

    # Transcribe each clip and generate captions
    # captioned_clips = []
    # for clip in clips:
    #     print(f"📄 Transcribing clip: {clip}")
    #     clip_transcript = transcribe_audio(clip, project_id, chunk_size=5.0)  # Transcribe only the clip
    #     if not clip_transcript:
    #         print(f"⚠️ No transcript generated for clip: {clip}")
    #         continue

    #     # Add captions to the clip in real-time
    #     caption_path = clip.replace(".mp4", "_captioned.mp4")
    #     add_captions_to_clip(clip, clip_transcript, caption_path)
    #     print(f"🎥 Captions added to clip: {caption_path}")
    #     captioned_clips.append(caption_path)

    return clips