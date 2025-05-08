# app/main.py
import logging
import os
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from fastapi.responses import HTMLResponse, JSONResponse
import shutil
import time
import psutil
from app.models.request import ClipRequest
from app.services.clip_service import process_video

# Initialize app
app = FastAPI(title="Clip Generator API", version="1.0.0")
templates = Jinja2Templates(directory="templates")
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
start_time = time.time()

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

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """
    Render status dashboard.
    """
    return templates.TemplateResponse("index.html", {"request": request, "status": "🟢 Server is running!"})


@app.get("/")
async def get_status(request: Request):
    uptime_seconds = int(time.time() - start_time)
    uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))

    server_status = "Running" if psutil.cpu_percent() < 90 else "Under Load"

    return templates.TemplateResponse("status.html", {
        "request": request,
        "uptime": uptime_str,
        "server_status": server_status
    })


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return JSONResponse(content={"filename": file.filename, "path": file_path})

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


