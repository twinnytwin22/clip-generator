import requests
import os
from config import OPENAI_API_KEY

def generate_clip_title(transcript_text):
    prompt = f"Generate a viral short video title and 3 hashtags for the following:\n\n{transcript_text[:1000]}"
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": prompt}]
    }

    res = requests.post("https://api.openai.com/v1/chat/completions", json=data, headers=headers)
    return res.json()["choices"][0]["message"]["content"]
