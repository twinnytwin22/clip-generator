import os
import re
import logging
import subprocess
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import yt_dlp  # Using yt-dlp for YouTube downloads
from clip_generator.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.getcwd()
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

class DownloadRequest(BaseModel):
    video_url: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # URL of the YouTube video to download
    quality: str = "720p"  # Requested video quality, e.g. "720p", "1080p"

router = APIRouter()

@router.post("/youtube", summary="Download YouTube Video", description="Downloads a YouTube video and returns its details")
async def download_youtube_video(req: DownloadRequest):
    logger.info("→ Request: video_url=%s, quality=%s", req.video_url, req.quality)

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
        ydl_opts = {
            'format': f'bestvideo[height<={req.quality.rstrip("p")}]+bestaudio/best[height<={req.quality.rstrip("p")}]/best',
            'outtmpl': os.path.join(OUTPUT_DIR, f'{youtube_id}.%(ext)s'),  # Use dynamic extension
            'merge_output_format': 'mp4',  # Try to merge to mp4 when possible
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
            
        # Check for files in the output directory that match this video ID
        # yt-dlp might save with different extensions or temp names
        matching_files = [f for f in os.listdir(OUTPUT_DIR) if youtube_id in f]
        
        if not matching_files:
            logger.error("✗ No files found for video ID: %s", youtube_id)
            raise HTTPException(500, "Downloaded file not found")
            
        # Find the largest file (most likely the complete video)
        largest_file = None
        largest_size = 0
        
        for filename in matching_files:
            file_path = os.path.join(OUTPUT_DIR, filename)
            if os.path.isfile(file_path):
                file_size = os.path.getsize(file_path)
                if file_size > largest_size:
                    largest_size = file_size
                    largest_file = file_path
        
        if largest_file:
            mp4_path = largest_file
            logger.info("✔ Download complete, found file: %s (%.1f MB)", mp4_path, largest_size/1e6)
        else:
            logger.error("✗ Could not determine main video file for ID: %s", youtube_id)
            raise HTTPException(500, "Could not determine downloaded file")

    # 4. Return video file details
    file_size = os.path.getsize(mp4_path) if os.path.exists(mp4_path) else 0
    
    return {
        "file_path": mp4_path,
        "video_id": youtube_id,
        "size_mb": round(file_size/1e6, 2)
    }
