import os
import re
import logging
import subprocess
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import yt_dlp  # Using yt-dlp for YouTube downloads
from clip_generator.app.models.request import ClipRequest
from clip_generator.app.api.generateClips import generate_clips
from clip_generator.utils.supabaseClient.supabase import supabase
from clip_generator.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_BUCKET = 'videos'
PROJECT_ROOT   = os.getcwd()
OUTPUT_DIR     = os.path.join(PROJECT_ROOT, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

class DownloadRequest(BaseModel):
    video_url: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # URL of the YouTube video to download
    title: str = "Example YouTube Video"  # Title for the video (used for clip generation)
    storage: str = "local"  # Where to store the video: "local" or "supabase"
    quality: str = "720p"  # Requested video quality
    profile_id: str = "user-profile-id"  # User profile ID (required for Supabase storage)
    video_id: str = "custom-video-id"  # Custom ID for the video

router = APIRouter()

@router.post("/clip-youtube-video", summary="Download YouTube Video", description="Download a YouTube video and prepare it for clip generation")
async def download_youtube_video(req: DownloadRequest):
    logger.info("→ Request: video_url=%s, storage=%s, quality=%s, video_id=%s", req.video_url, req.storage, req.quality, req.video_id)

    # 1. Extract YouTube video ID
    youtube_id_match = re.search(r"(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)", req.video_url)
    if not youtube_id_match:
        logger.error("✗ Invalid YouTube video URL: %s", req.video_url)
        raise HTTPException(400, "Invalid YouTube video URL")
    youtube_id = youtube_id_match.group(1)
    logger.info("✔ YouTube ID: %s", youtube_id)

    mp4_path = os.path.join(OUTPUT_DIR, f"{youtube_id}.mp4")

    # 2. Check if already downloaded
    if os.path.exists(mp4_path):
        logger.info("✔ Video already downloaded at %s", mp4_path)
    else:
        # 3. Download if not present using yt-dlp
        logger.info("→ Downloading YouTube video with ID: %s", youtube_id)
        
        # Configure yt-dlp options with fallbacks and better error handling
        # Configure yt-dlp options with fallbacks and better error handling
        ydl_opts = {
            'format': f'bestvideo[height<={req.quality.rstrip("p")}]+bestaudio/best[height<={req.quality.rstrip("p")}]/best',
            'outtmpl': mp4_path,
            'quiet': False,  # Set to False to see download progress
            'no_warnings': False,  # Set to False to see warnings
            'ignoreerrors': False,  # Don't ignore errors
            'nocheckcertificate': True,  # Skip HTTPS certificate validation
            'geo_bypass': True,  # Try to bypass geographic restrictions
            'extractor_retries': 3,  # Retry extraction 3 times
            'retries': 5,  # Retry download 5 times
            'fragment_retries': 5,  # Retry fragments 5 times
            'sleep_interval': 5,  # Sleep 5 seconds between retries
            'max_sleep_interval': 30,  # Maximum sleep of 30 seconds
            'verbose': True,  # Show detailed messages
            'progress_hooks': [(lambda d: logger.info('… downloaded %.1f%%', 
                                                    d['downloaded_bytes'] * 100 / d['total_bytes'] 
                                                    if d.get('total_bytes') else -1) 
                              if d['status'] == 'downloading' and d.get('downloaded_bytes') else None)],
        }
        
        def sync_download():
            try:
                logger.info("Starting YouTube download with yt-dlp...")
                
                # Use Google API key if available
                api_key = getattr(settings, 'GOOGLE_API_KEY', None)
                if api_key:
                    logger.info("Using Google API key for YouTube access")
                    ydl_opts['ap_mso'] = api_key
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(req.video_url, download=False)
                    if info:
                        logger.info(f"Video found: {info.get('title')} ({info.get('duration_string')})")
                        available_formats = [f"{f['format_id']} - {f.get('height', 'N/A')}p" for f in info.get('formats', []) if f.get('height')]
                        logger.info(f"Available qualities: {', '.join(available_formats[:5])}...")
                    
                    # Actually download the video
                    ydl.download([req.video_url])
                return True
            except yt_dlp.utils.DownloadError as e:
                logger.exception("✗ YouTube download error")
                if "Private video" in str(e):
                    raise HTTPException(403, "Cannot download private video")
                elif "not available" in str(e):
                    raise HTTPException(404, "Video not available")
                else:
                    raise HTTPException(400, f"Download failed: {str(e)}")
            except Exception as e:
                logger.exception("✗ Unexpected error during download")
                raise HTTPException(500, f"Unexpected error: {str(e)}")
                
        success = await run_in_threadpool(sync_download)
        if not success:
            raise HTTPException(500, "Error downloading YouTube video")
        logger.info("✔ Download complete, file size: %.1f MB", os.path.getsize(mp4_path)/1e6)

    # 4. Optionally upload to Supabase (if requested)
    if req.storage.lower() == "supabase":
        logger.info("→ Uploading %s to Supabase bucket '%s'", mp4_path, SUPABASE_BUCKET)
        if not supabase:
            logger.error("✗ Supabase not configured")
            raise HTTPException(500, "Supabase not configured")
        with open(mp4_path, "rb") as f:
            data = f.read()
        res = supabase.storage.from_(SUPABASE_BUCKET).upload(f"{req.profile_id}/{youtube_id}.mp4", data)
        if res.get("error"):
            logger.error("✗ Supabase upload error: %s", res['error']['message'])
            raise HTTPException(500, f"Supabase upload failed: {res['error']['message']}")
        url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(f"{req.profile_id}/{youtube_id}.mp4")["publicURL"]
        logger.info("✔ Uploaded, public URL: %s", url)
        return {"url": url}

    # 5. Start generate_clips in the background
    clipRequestData = ClipRequest(
        filename=mp4_path,
        profile_id=req.profile_id,
        title=req.title,
        video_id=req.video_id,
    )

    asyncio.create_task(generate_clips(clipRequestData))
    logger.info("Clips generation for this video has started.")

    # 6. Return local path immediately
    return {"local_path": mp4_path}
