import logging
import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import shutil

from app.models.request import ClipRequest
from app.services.clip_service import process_video
from app.api.status import router as status_router
from app.api.generateClips import router as generateClips

# Initialize app
app = FastAPI(title="Clip Generator API", version="1.0.0")
app.include_router(status_router)
app.include_router(generateClips)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)




