from fastapi import APIRouter, Request
import time
import psutil
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse  
import logging
console = logging.getLogger()

router = APIRouter()
templates = Jinja2Templates(directory="templates")
start_time = time.time()

@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Render status dashboard.
    """
    # Get uptime
    uptime_seconds = int(time.time() - start_time)
    uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))

    # Get server status
    server_status = "Running" if psutil.cpu_percent() < 90 else "Under Load"

    # Render template with dynamic data
    return templates.TemplateResponse("index.html", {
        "request": request,
        "uptime": uptime_str,
        "server_status": server_status,
       // "console_logs": console.handlers[0].stream.getvalue().splitlines()[-20:] 
          # Get last 20 lines
    })
