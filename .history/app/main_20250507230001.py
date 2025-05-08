# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from app.models.request import ClipRequest
from app.services.clip_service import process_video

app = FastAPI(title="Clip Generator API", version="1.0.0")
templates = Jinja2Templates(directory="templates")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development; use specific origins in production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

@app.get("/")
def root():
    return {"status": "Clip Generator is live."}

@app.post("/generate-clips")
def generate_clips(request: ClipRequest):
    try:
        result = process_video(request.filename)
        return {"message": "✅ Processing complete", "clips": result}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error: {str(e)}")
