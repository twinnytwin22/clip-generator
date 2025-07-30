from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime


class Profile(BaseModel):
    id: UUID
    username: Optional[str]
    full_name: Optional[str]
    avatar_url: Optional[str]
    website: Optional[str]
    metadata: Optional[Dict[str, Any]] = {}
    updated_at: Optional[datetime]


class Clip(BaseModel):
    id: UUID
    project_id: UUID
    start_time: float
    end_time: float
    caption: Optional[str]
    file_url: str
    metadata: Optional[Dict[str, Any]] = {}
    created_at: datetime


class Project(BaseModel):
    id: UUID
    profile_id: UUID
    title: Optional[str]
    video_url: str
    metadata: Optional[Dict[str, Any]] = {}
    created_at: datetime
    clips: Optional[List[Clip]] = []
    status: Optional[str] = "processing"  # Default status
