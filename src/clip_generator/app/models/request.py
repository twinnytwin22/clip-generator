# app/models/request.py
import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class ClipRequest(BaseModel):
    
    filename: str 
    profile_id: str  # e.g., "123e4567-e89b-12d3-a456-426614174000"
     # e.g., "video.mp4"
    # start_time : float  # e.g., 0.0 
    # end_time: float  # e.g., 10.0
    title: Optional[Any] = "Video-" + str(uuid.uuid4())  # e.g., "My Clip Title"
    video_id: str
    # caption: str  # e.g., "This is a caption for the clip." 