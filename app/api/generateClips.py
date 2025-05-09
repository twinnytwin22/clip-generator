from fastapi import APIRouter, HTTPException
import logging

from app.models.request import ClipRequest
from app.services.clip_service import process_video

logger = logging.getLogger(__name__)
router = APIRouter()

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
    except ValueError as ve:
        logger.error(f"Invalid file: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.exception("Unexpected error during clip processing.")
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")