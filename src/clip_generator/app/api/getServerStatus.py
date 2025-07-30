from fastapi import APIRouter
import time
import psutil
from clip_generator.utils.supabaseClient.supabase import supabase

clips = supabase.storage.from_("clips").list()
router = APIRouter()
start_time = time.time()

@router.get("/getServerStatus")
async def api_status():
    """
    Endpoint to get server status and uptime.
    """
    uptime_seconds = int(time.time() - start_time)
    uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))
    server_status = "Running" if psutil.cpu_percent() < 90 else "Under Load"
    print(clips, 'CLIPS BUCKET')
    return {"uptime": uptime_str, "server_status": server_status}