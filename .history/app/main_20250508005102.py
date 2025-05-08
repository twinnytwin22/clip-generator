import logging
import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import shutil

from app.models.request import ClipRequest
from app.services.clip_service import process_video
from app.api.status import router as status_router

# Initialize app
app = FastAPI(title="Clip Generator API", version="1.0.0")
app.include_router(status_router)

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




@app.post("/generate-clips")
async def generate_clips(request_data: ClipRequest):
    """
    Handle clip generation from uploaded video filename.
    """
    try:
        logger.info(f"Processing video: {request_data.filename}")
        result = process_video(request_data.filename)
        return {"message": "✅ Processing complete", "clips": result}
    except FileNotFoundError:
        logger.error(f"File not found: {request_data.filename}")
        raise HTTPException(status_code=404, detail="File not found.")
    except Exception as e:
        logger.exception("Unexpected error during clip processing.")
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")
