# app/main.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from models.request import ClipRequest
from services.clip_service import process_video
import os

app = FastAPI(title="Clip Generator API", version="1.0.0")

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
