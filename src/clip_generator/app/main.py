import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from importlib import resources
from clip_generator.app.api.getServerStatus import router as getServerStatus
from clip_generator.app.api.generateClips import router as generateClips
from clip_generator.app.api.upload import router as upload_router
from clip_generator.app.api.downloadTwitchVOD import router as downloadTwitchVOD
from clip_generator.app.api.downloadYoutubeVOD import router as downloadYoutubeVOD
# Initialize app
app = FastAPI(title="Subport: StreamTools API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(getServerStatus, prefix="/api")
app.include_router(generateClips)
app.include_router(upload_router)
app.include_router(downloadTwitchVOD)
# Add YouTube router with explicit path and tags
app.include_router(downloadYoutubeVOD, tags=["youtube"], prefix="")

# Serve the index.html file
@app.get("/")
async def serve_index():
    with resources.path("clip_generator", "index.html") as fp:
        return FileResponse(fp)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Enable CORS

UPLOAD_DIR = "uploads"
CLIPS_DIR = "clips"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CLIPS_DIR, exist_ok=True)



