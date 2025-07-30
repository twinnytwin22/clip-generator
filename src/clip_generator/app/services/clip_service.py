import requests
import os
from clip_generator.config import INPUT_DIR
from clip_generator.utils.transcription import transcribe_audio
from clip_generator.utils.clipper import cut_clips
from clip_generator.utils.supabaseClient.supabase import supabase

MAX_CLIPS = 3
MIN_WORDS = 20
CHUNK_SIZE = 30.0  # seconds

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

    # If the file already exists locally, just return it
    if os.path.isfile(local_path):
        print(f"✅ File already exists locally: {local_path}")
        return local_path

    # Get a signed URL if profile_id is provided (indicating a private file)
    if profile_id:
        print(f"🔐 Generating signed URL for: {path_in_bucket}")
        result = supabase.storage.from_("uploads").create_signed_url(path_in_bucket, 3600)
        print(f"🔐 Signed URL: {result}")
        url_to_download = result.get("signedURL")
    else:
        raise ValueError("Public URL access is not supported in this context.")

    print(f"⬇️ Downloading: {url_to_download}")
    with requests.get(url_to_download, stream=True) as r:
        r.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    print(f"✅ File saved: {local_path}")
    return local_path

def process_video(filename: str, project_id: str, profile_id: str):
    """
    Process a video file to generate clips with captions.

    Args:
        filename (str): Path to the video file or Supabase path.
        min_words (int): Minimum number of words required in a segment to create a clip.
        max_clips (int): Maximum number of clips to create.

    Returns:
        dict: Result from cut_clips (clips and status).
    """
    # If the filename is a local file, use it directly
    if os.path.isfile(filename):
        full_path = filename
        print(f"Using local file: {full_path}")
    else:
        # Otherwise, treat as a Supabase path and download
        print("Downloading file from Supabase...")
        full_path = download_file(filename, profile_id, INPUT_DIR)
        print(f"Downloaded file to: {full_path}")

    if not os.path.isfile(full_path):
        raise FileNotFoundError(f"{full_path} not found.")

    # Transcribe the entire video to identify segments
    print("Transcribing video...")
    audio = transcribe_audio(full_path, project_id, profile_id, CHUNK_SIZE)

    projectTranscript = audio.get("transcript")
    if not projectTranscript:
        raise ValueError("No transcript generated. Please check the video file.")

    print("✂️ Cutting clips...")
    clips = cut_clips(full_path, projectTranscript, project_id, MIN_WORDS, MAX_CLIPS)
    if not clips.get('status') == "ready":
        raise ValueError("No clips generated. Please check the video file or criteria.")
    print(f"✅ Clips created: {clips}")

    return clips