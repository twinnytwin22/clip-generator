import os
from clip_generator.config import OUTPUT_DIR
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.fx.all import crop
from moviepy.video.fx.resize import resize
from clip_generator.utils.supabaseClient.supabase import supabase
from clip_generator.utils.scene_detection import detect_scenes_pyscenedetect

def cut_clips(filepath, transcript, project_id, min_words=5, max_clips=1, crop_width=720, crop_height=1280):
    """
    Cut and vertically crop video clips, generate thumbnails, save them to Supabase,
    and return the clips with a status of 'ready'.

    Args:
        filepath (str): Path to the video file.
        transcript (list): List of transcript segments with 'start', 'end', and 'text'.
        project_id (str): ID of the project in Supabase.
        min_words (int): Minimum number of words required in a segment to create a clip.
        max_clips (int): Maximum number of clips to create (optional).
        crop_width (int): Width of the cropped video (default: 720 for vertical format).
        crop_height (int): Height of the cropped video (default: 1280 for vertical format).

    Returns:
        dict: A dictionary containing the list of clip metadata and a status of 'ready'.
    """

    scenes = detect_scenes_pyscenedetect(filepath)

    # Validate transcript format

    if not isinstance(transcript, list) or not all(isinstance(seg, dict) for seg in transcript):
        raise ValueError("Invalid transcript format. Expected a list of dictionaries with 'start', 'end', and 'text' keys.")

    # Ensure the video file exists
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Video file not found: {filepath}")

    # Ensure the output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    clips = []
    try:
        video = VideoFileClip(filepath)
    except Exception as e:
        raise RuntimeError(f"Failed to load video file: {e}")

    for i, seg in enumerate(transcript):
        # Skip segments with fewer words than the minimum required
        if len(seg["text"].split()) < min_words:
            print(f"Skipping segment {i}: Not enough words ({len(seg['text'].split())} < {min_words})")
            continue

        # Stop if the maximum number of clips has been reached
        if max_clips is not None and len(clips) >= max_clips:
            print(f"Reached maximum number of clips: {max_clips}")
            break

        start, end = seg["start"], seg["end"]
        print(f"Processing segment {i}: Start={start}, End={end}, Text={seg['text']}")

        try:
            # Extract the clip
            clip = video.subclip(start, end)

            # Resize wide videos to ensure vertical crop is possible
            if clip.w < crop_width or clip.h < crop_height:
                print(f"Resizing clip {i} to ensure vertical crop is possible.")
                clip = resize(clip, height=max(crop_height, clip.h))

            # Smart crop: vertical format, center-focused
            x_center = clip.w / 2
            y_center = clip.h / 2

            if clip.w > clip.h:  # Landscape video
                print(f"Cropping horizontal video {i} to vertical center.")
            else:
                print(f"Video {i} is already portrait or square.")

            cropped_clip = crop(
                clip,
                x_center=x_center,
                y_center=y_center,
                width=crop_width,
                height=crop_height
            )

            # Output file
            out_path = os.path.join(OUTPUT_DIR, f"clip_{i}.mp4")
            print(f"Saving clip {i} to {out_path}")
            cropped_clip.write_videofile(
                out_path,
                codec="libx264",
                audio_codec="aac",  # Ensure audio is included
                preset="medium",
                threads=4,
                fps=clip.fps
            )

            # Generate thumbnail
            thumbnail_path = os.path.join(OUTPUT_DIR, f"thumbnail_{i}.jpg")
            midpoint = (start + end) / 2  # Get the midpoint of the clip
            print(f"Generating thumbnail for clip {i} at {midpoint} seconds.")
            clip.save_frame(thumbnail_path, t=midpoint)

            # Save clip and transcript to Supabase
            clip_metadata = save_clip_to_supabase(project_id, out_path, thumbnail_path, seg["text"], start, end)
            if clip_metadata:
                clips.append(clip_metadata)

        except Exception as e:
            print(f"❌ Failed to process segment {i}: {e}")

    video.close()
    print(f"✅ All clips processed. Total clips: {len(clips)}")
    return {"clips": clips, "status": "ready"}


def save_clip_to_supabase(project_id, clip_path, thumbnail_path, transcript, start, end):
    """
    Save the clip, its thumbnail, and its transcript to Supabase using a signed URL upload strategy.

    Args:
        project_id (str): ID of the project in Supabase.
        clip_path (str): Local file path of the clip.
        thumbnail_path (str): Local file path of the thumbnail.
        transcript (str): Transcript associated with the clip.
        start (float): Start time of the clip in seconds.
        end (float): End time of the clip in seconds.

    Returns:
        dict: Metadata for the uploaded clip.
    """
    bucket_name = "clips"
    clip_filename = os.path.basename(clip_path)
    thumbnail_filename = os.path.basename(thumbnail_path)

    try:
        # Upload clip
        clip_upload_path = os.path.join(project_id, clip_filename)
        clip_signed_url = supabase.storage.from_(bucket_name).create_signed_upload_url(clip_upload_path)
        clip_token = clip_signed_url.get("token")
        if not clip_token:
            raise ValueError("Failed to retrieve the token for the clip upload.")

        with open(clip_path, "rb") as clip_file:
            supabase.storage.from_(bucket_name).upload_to_signed_url(
                path=clip_upload_path,
                file=clip_file,
                token=clip_token
            )

        # Upload thumbnail
        thumbnail_upload_path = os.path.join(project_id, thumbnail_filename)
        thumbnail_signed_url = supabase.storage.from_('thumbnails').create_signed_upload_url(thumbnail_upload_path)
        thumbnail_token = thumbnail_signed_url.get("token")
        if not thumbnail_token:
            raise ValueError("Failed to retrieve the token for the thumbnail upload.")

        with open(thumbnail_path, "rb") as thumbnail_file:
            supabase.storage.from_('thumbnails').upload_to_signed_url(
                path=thumbnail_upload_path,
                file=thumbnail_file,
                token=thumbnail_token
            )

        # Save metadata to Supabase
        metadata_response = supabase.table("clips").insert({
            "project_id": project_id,
            "file_url": clip_upload_path,
            "thumbnail_url": thumbnail_upload_path,
            "transcript": transcript,
            "start_time": start,
            "end_time": end
        }).execute()

        if metadata_response:
            print(f"✅ Clip and thumbnail metadata successfully saved to Supabase for project {project_id}.")
            return {
                "project_id": project_id,
                "file_url": clip_upload_path,
                "thumbnail_url": thumbnail_upload_path,
                "transcript": transcript,
                "start_time": start,
                "end_time": end
            }
        else:
            print(f"❌ Failed to save clip metadata to Supabase: {metadata_response}")
    except Exception as e:
        print(f"❌ An error occurred while uploading the clip or thumbnail: {e}")
    return None