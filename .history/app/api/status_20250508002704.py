import logging
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import time
import psutil

app = FastAPI(title="Clip Generator API", version="1.0.0")
templates = Jinja2Templates(directory="templates")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
start_time = time.time()

@app.get("/", response_class=HTMLResponse)
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
        "server_status": server_status
    })


