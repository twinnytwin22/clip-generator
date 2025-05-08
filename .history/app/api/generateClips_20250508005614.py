from fastapi import APIRouter, HTTPException, Request, logger
import time
import psutil
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse  
import logging

from app.models.request import ClipRequest
from app.services.clip_service import process_video
console = logging.getLogger()

router = APIRouter()
templates = Jinja2Templates(directory="templates")
start_time = time.time()




@router.post("/generate-clips")
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

