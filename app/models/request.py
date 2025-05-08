# app/models/request.py
from pydantic import BaseModel

class ClipRequest(BaseModel):
    filename: str  # e.g., "video.mp4"
    start_time : float  # e.g., 0.0 
    end_time: float  # e.g., 10.0
    title: str  # e.g., "My Clip Title"
    caption: str  # e.g., "This is a caption for the clip."