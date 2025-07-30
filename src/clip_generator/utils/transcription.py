import os
from tempfile import NamedTemporaryFile

from faster_whisper import WhisperModel
from moviepy.video.io.VideoFileClip import VideoFileClip

from clip_generator.utils.supabaseClient.save_srt import save_srt_to_supabase
from clip_generator.utils.convertto_srt import convert_to_srt
from clip_generator.utils.supabaseClient.supabase import supabase


def transcribe_audio(video_path: str, project_id: str, profile_id: str, chunk_size: float) -> str:
    """Transcribe audio from a video file and store the transcript on Supabase."""
    model = WhisperModel("base", device="cpu")
    transcript = []

    with VideoFileClip(video_path) as video:
        audio = video.audio
        duration = audio.duration

        print("Starting real-time transcription...")
        for start_time in range(0, int(duration), int(chunk_size)):
            end_time = min(start_time + chunk_size, duration)
            with NamedTemporaryFile(suffix=".wav", delete=False) as tmp_audio:
                audio_chunk_path = tmp_audio.name
            audio.subclip(start_time, end_time).write_audiofile(
                audio_chunk_path, fps=16000, codec="pcm_s16le"
            )

            segments, _ = model.transcribe(audio_chunk_path)
            for segment in segments:
                if segment.words:
                    for word in segment.words:
                        transcript.append({
                            "start": word.start + start_time,
                            "end": word.end + start_time,
                            "text": word.word,
                        })
                else:
                    transcript.append({
                        "start": segment.start + start_time,
                        "end": segment.end + start_time,
                        "text": segment.text,
                    })
            os.remove(audio_chunk_path)
            print(f"Processed chunk: {start_time}-{end_time} seconds")
        print("Real-time transcription complete.")

    srt_content = convert_to_srt(transcript)
    srt_file_path = save_srt_to_supabase(project_id, profile_id, srt_content)
    update_status_in_supabase(project_id, "processing", srt_file_path)

    return {
        "project_id": project_id,
        "srt_file_path": srt_file_path,
        "status": "processing",
        "transcript": transcript,
    }


def update_status_in_supabase(project_id: str, status: str, srt_file_path: str) -> None:
    """Update the status and SRT file path for a project in Supabase."""
    response = (
        supabase.table("projects")
        .update({"status": status, "srt_file_path": srt_file_path})
        .eq("id", project_id)
        .execute()
    )
    if response:
        print("✅ Status successfully updated in Supabase.")
    else:
        print(f"❌ Failed to update status in Supabase: {response}")

