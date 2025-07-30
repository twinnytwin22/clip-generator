from fastapi import APIRouter, HTTPException
import logging
from app.models.request import ClipRequest
from app.services.clip_service import process_video
from clip_generator.utils.supabaseClient.supabase import supabase


logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/generate-clips")
async def generate_clips(request_data: ClipRequest):
    """
    Handle clip generation from uploaded video filename.
    Also creates a project record in Supabase and updates its status.
    """
    try:
        # Create project with 'processing' status
        insert_resp = supabase.table("projects").insert({
            "profile_id": request_data.profile_id,
            "video_url": request_data.filename,
            "title": "Video 2",
            "status": "processing"
        }).execute()
        #print(insert_resp)
        if insert_resp.data[0]["id"] == None:
           # logger.error(f"Failed to insert project: {insert_resp.error.message}")
            raise HTTPException(status_code=500, detail="Failed to create project")

        project_id = insert_resp.data[0]["id"]
        profile_id = request_data.profile_id

    except Exception as e:
        logger.exception("Failed to create project in Supabase")
        raise HTTPException(status_code=500, detail="Failed to create project")

    try:
        logger.info(f"Processing video: {request_data.filename}")
        result = process_video(request_data.filename, project_id, profile_id)
        print("process_video result", result)
        if result.get("status") != "ready":
            raise HTTPException(status_code=500, detail="Video processing failed")
        # Update project to 'complete'
        supabase.table("projects").update({
            "status": "completed"
        }).eq("id", project_id).execute()

        clips = result.get("clips", [])
        if not clips:
            raise HTTPException(status_code=500, detail="No clips generated")

        supabase.table("clips").insert(clips).execute()

        return {
            "message": "✅ Processing complete",
            "clips": result,
            "project_id": project_id
        }

    except Exception as e:
        logger.exception("Clip generation failed")

        # Update project to 'failed'
        supabase.table("projects").update({
            "status": "failed"
        }).eq("id", project_id).execute()

        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
