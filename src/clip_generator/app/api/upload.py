from fastapi import APIRouter, UploadFile, File
import os
from clip_generator.config import INPUT_DIR

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(INPUT_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"message": "File uploaded successfully", "filename": file.filename}