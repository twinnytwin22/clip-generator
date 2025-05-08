# app/models/request.py
from pydantic import BaseModel

class ClipRequest(BaseModel):
    filename: str  # e.g., "video.mp4"
