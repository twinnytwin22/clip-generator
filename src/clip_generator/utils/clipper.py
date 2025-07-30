import os
from clip_generator.config import OUTPUT_DIR
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.fx.all import crop
from moviepy.video.fx.resize import resize
from clip_generator.utils.supabaseClient.supabase import supabase
from clip_generator.utils.scene_detection import detect_scenes_local


MAX_CLIPS = 3
MIN_WORDS = 20
CHUNK_SIZE = 30.0  # seconds
CROP_W, CROP_H = 720, 1280


def cut_clips(filepath,
              transcript,
              project_id,
              min_words=MIN_WORDS,
              max_clips=MAX_CLIPS,
              crop_width=CROP_W,
              crop_height=CROP_H):
    # 1) detect your shot boundaries
    scenes = detect_scenes_local(filepath)

    # 2) index transcript by time for quick lookup
    #    flatten segments into (time, word_count) points
    word_events = []
    for seg in transcript:
        start, end, text = seg["start"], seg["end"], seg["text"]
        wc = len(text.split())
        # we'll assign all words in this segment to its midpoint
        mid = (start + end) / 2
        word_events.append((mid, wc))

    def words_in_scene(t0, t1):
        return sum(wc for t, wc in word_events if t0 <= t <= t1)

    # 3) iterate scenes, pick the best ones
    clips, video = [], VideoFileClip(filepath)
    for i, (t0, t1) in enumerate(scenes):
        if len(clips) >= max_clips:
            break

        wc = words_in_scene(t0, t1)
        if wc < min_words:
            print(f"Scene {i} ({t0:.1f}-{t1:.1f}s) skipped ({wc} words)")
            continue

        print(f"Scene {i} accepted ({t0:.1f}-{t1:.1f}s, {wc} words) → cutting clip")
        clip = video.subclip(t0, t1)

        # ensure we can crop to vertical
        if clip.w < crop_width or clip.h < crop_height:
            clip = resize(clip, height=max(clip.h, crop_height))

        x_c, y_c = clip.w/2, clip.h/2
        cropped = crop(clip,
                       x_center=x_c,
                       y_center=y_c,
                       width=crop_width,
                       height=crop_height)

        out_path = os.path.join(OUTPUT_DIR, f"clip_{i}.mp4")
        cropped.write_videofile(out_path,
                                codec="libx264",
                                audio_codec="aac",
                                preset="medium",
                                threads=4,
                                fps=clip.fps)

        thumb = os.path.join(OUTPUT_DIR, f"thumb_{i}.jpg")
        cropped.save_frame(thumb, t=(t0 + t1)/2)

        meta = save_clip_to_supabase(project_id,
                                     out_path,
                                     thumb,
                                     "",  # you can join transcripts inside [t0,t1] if you like
                                     t0, t1)
        if meta:
            clips.append(meta)

    video.close()
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