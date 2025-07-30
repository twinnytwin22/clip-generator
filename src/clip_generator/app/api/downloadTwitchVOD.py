import os
import re
import logging
import subprocess
import concurrent.futures
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from streamlink import Streamlink, StreamError
from clip_generator.app.models.request import ClipRequest
from clip_generator.app.api.generateClips import generate_clips
from clip_generator.utils.supabaseClient.supabase import supabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPABASE_BUCKET = 'videos'
PROJECT_ROOT   = os.getcwd()
OUTPUT_DIR     = os.path.join(PROJECT_ROOT, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

class DownloadRequest(BaseModel):
    vod_url: str
    title: str
    storage: str = "local"
    quality: str = "720p"
    profile_id: str

router = APIRouter()

def run_generate_clips(request_data: ClipRequest):
    # If generate_clips is async, run it in an event loop
    asyncio.run(generate_clips(request_data))

@router.post("/download-twitch-vod")
async def download_vod(req: DownloadRequest):
    logger.info("→ Request: vod_url=%s, storage=%s, quality=%s", req.vod_url, req.storage, req.quality)

    # 1. Extract VOD ID
    match = re.search(r"twitch\.tv/videos/(\d+)", req.vod_url)
    if not match:
        logger.error("✗ Invalid Twitch VOD URL: %s", req.vod_url)
        raise HTTPException(400, "Invalid Twitch VOD URL")
    vod_id = match.group(1)
    logger.info("✔ VOD ID: %s", vod_id)

    mp4_path = os.path.join(OUTPUT_DIR, f"{vod_id}.mp4")

    # 2. Check if already downloaded
    if os.path.exists(mp4_path):
        logger.info("✔ Video already downloaded at %s", mp4_path)
    else:
        # 3. Download if not present
        session = Streamlink()
        logger.info("→ Resolving streams for %s", req.vod_url)
        try:
            streams = session.streams(req.vod_url)
        except StreamError as e:
            logger.exception("✗ Streamlink resolution error")
            raise HTTPException(400, f"Stream resolution failed: {e}")
        if not streams:
            logger.warning("✗ No playable streams found")
            raise HTTPException(404, "No playable streams found")
        logger.info("✔ Qualities: %s", ", ".join(streams.keys()))

        stream = streams.get(req.quality) or streams.get("best")
        chosen = req.quality if req.quality in streams else "best"
        logger.info("✔ Selected quality: %s", chosen)

        ts_path  = os.path.join(OUTPUT_DIR, f"{vod_id}.ts")
        logger.info("→ Downloading TS to %s", ts_path)

        def sync_download():
            fd = stream.open()
            total_bytes = 0
            try:
                with open(ts_path, "wb") as out_file:
                    last_logged_mb = 0
                    while True:
                        chunk = fd.read(1024*1024)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        total_bytes += len(chunk)
                        current_mb = total_bytes // (5 * 1024 * 1024)
                        if current_mb > last_logged_mb:
                            logger.info("… downloaded %d MB", current_mb * 5)
                            last_logged_mb = current_mb
            finally:
                fd.close()
            logger.info("✔ TS download complete: %d MB", total_bytes//(1024*1024))

        await run_in_threadpool(sync_download)

        # Remux TS → MP4
        logger.info("→ Remuxing to MP4 at %s", mp4_path)
        ff = subprocess.run(
            ["ffmpeg", "-y", "-i", ts_path, "-c", "copy", mp4_path],
            capture_output=True, text=True
        )
        if ff.returncode != 0:
            logger.error("✗ FFmpeg error: %s", ff.stderr.strip())
            raise HTTPException(500, "Error converting TS to MP4")
        logger.info("✔ Remux complete, file size: %.1f MB", os.path.getsize(mp4_path)/1e6)

        try:
            os.remove(ts_path)
        except OSError:
            logger.warning("Could not remove temp TS file: %s", ts_path)

    # 4. Optionally upload to Supabase (if requested)
    if req.storage.lower() == "supabase":
        logger.info("→ Uploading %s to Supabase bucket '%s'", mp4_path, SUPABASE_BUCKET)
        if not supabase:
            logger.error("✗ Supabase not configured")
            raise HTTPException(500, "Supabase not configured")
        with open(mp4_path, "rb") as f:
            data = f.read()
        res = supabase.storage.from_(SUPABASE_BUCKET).upload(f"{req.profile_id}/{vod_id}.mp4", data)
        if res.get("error"):
            logger.error("✗ Supabase upload error: %s", res['error']['message'])
            raise HTTPException(500, f"Supabase upload failed: {res['error']['message']}")
        url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(f"{req.profile_id}{vod_id}.mp4")["publicURL"]
        logger.info("✔ Uploaded, public URL: %s", url)
        return {"url": url}

    # 5. Start generate_clips in the background
    clipRequestData = ClipRequest(
        filename=mp4_path,
        profile_id=req.profile_id,
        title=req.title
    )
    
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    executor.submit(run_generate_clips, clipRequestData)
    logger.info("Clips generation for this video has started.")

    # 6. Return local path immediately
    return {"local_path": mp4_path}