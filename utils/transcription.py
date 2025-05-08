from faster_whisper import WhisperModel

model = WhisperModel("base", compute_type="auto")

def transcribe_audio(filepath):
    segments, info = model.transcribe(filepath)
    transcript = []
    for segment in segments:
        transcript.append({
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip()
        })
    return transcript
