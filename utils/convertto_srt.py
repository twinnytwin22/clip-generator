def convert_to_srt(transcript: list) -> str:
    """
    Convert the transcript to SRT format.

    Args:
        transcript (list): List of transcript segments.

    Returns:
        str: Transcript in SRT format.
    """
    srt_output = []
    for i, seg in enumerate(transcript, start=1):
        start_time = seg["start"]
        end_time = seg["end"]
        text = seg["text"]

        # Convert seconds to SRT time format (HH:MM:SS,ms)
        start_srt = f"{int(start_time // 3600):02}:{int((start_time % 3600) // 60):02}:{int(start_time % 60):02},{int((start_time % 1) * 1000):03}"
        end_srt = f"{int(end_time // 3600):02}:{int((end_time % 3600) // 60):02}:{int(end_time % 60):02},{int((end_time % 1) * 1000):03}"

        srt_output.append(f"{i}\n{start_srt} --> {end_srt}\n{text}\n")

    return "\n".join(srt_output)

