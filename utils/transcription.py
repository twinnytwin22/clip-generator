import os
from faster_whisper import WhisperModel
from utils.supabaseClient.save_srt import save_srt_to_supabase  # Supabase client instance
from utils.convertto_srt import convert_to_srt  # Function to convert transcript to SRT format
from utils.supabaseClient.supabase import supabase


def transcribe_audio(video_path: str, project_id: str, profile_id:str, chunk_size: float) -> str:
    """
    Transcribe audio from a video file, convert it to SRT, save it to Supabase, and update the status.

    Args:
        video_path (str): Path to the video file.
        project_id (str): ID of the project in Supabase.
        chunk_size (float): Duration of each audio chunk to process in seconds.

    Returns:
        str: Status of the transcription process ("ready" or "failed").
    """
    model = WhisperModel("base", device="cpu")  # Use "cuda" for GPU acceleration if available

    # Open the video file and extract audio
    from moviepy.video.io.VideoFileClip import VideoFileClip
    video = VideoFileClip(video_path)
    audio = video.audio

    # Prepare for real-time transcription
    duration = audio.duration
    transcript = []

    print("Starting real-time transcription...")
    for start_time in range(0, int(duration), int(chunk_size)):
        end_time = min(start_time + chunk_size, duration)
        audio_chunk_path = f"temp_audio_{start_time}_{end_time}.wav"

        # Export the audio chunk
        audio.subclip(start_time, end_time).write_audiofile(audio_chunk_path, fps=16000, codec="pcm_s16le")

        # Transcribe the audio chunk
        segments, _ = model.transcribe(audio_chunk_path)

        for segment in segments:
            # Check if word-level timing is available
            if segment.words:
                for word in segment.words:
                    transcript.append({
                        "start": word.start + start_time,
                        "end": word.end + start_time,
                        "text": word.word
                    })
            else:
                # Fallback to segment-level timing if word-level timing is unavailable
                transcript.append({
                    "start": segment.start + start_time,
                    "end": segment.end + start_time,
                    "text": segment.text
                })

        # Clean up temporary audio file
        os.remove(audio_chunk_path)

        print(f"Processed chunk: {start_time}-{end_time} seconds")

    print("Real-time transcription complete.")

    # Convert transcript to SRT format
    srt_content = convert_to_srt(transcript)

    # Save SRT to Supabase
    srt_file_path = save_srt_to_supabase(project_id, profile_id, srt_content)

    # Update the status in Supabase
    update_status_in_supabase(project_id, "processing", srt_file_path)

    result = {
        "project_id": project_id,
        "srt_file_path": srt_file_path,
        "status": "processing", 
        "transcript": transcript
    }

    return result


def update_status_in_supabase(project_id: str, status: str, srt_file_path: str):
    """
    Update the status and SRT file path in the Supabase database.

    Args:
        project_id (str): ID of the project in Supabase.
        status (str): Status of the transcription process ("ready" or "failed").
        srt_file_path (str): Path to the SRT file in Supabase storage.
    """
    response = supabase.table("projects").update({
        "status": status,
        "srt_file_path": srt_file_path
    }).eq("id", project_id).execute()

    if response:
        print("✅ Status successfully updated in Supabase.")
    else:
        print(f"❌ Failed to update status in Supabase: {response}")