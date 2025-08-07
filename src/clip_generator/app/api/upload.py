from fastapi import APIRouter, UploadFile, File
import os
from pathlib import Path
from clip_generator.config import INPUT_DIR

router = APIRouter()


def _safe_path(filename: str) -> Path:
    """Return a safe path within ``INPUT_DIR`` for the given filename.

    Only the base name of ``filename`` is used to avoid directory traversal
    attacks.  The resulting path is validated to ensure it resides inside the
    uploads directory.
    """

    safe_name = Path(filename).name
    target_path = Path(INPUT_DIR) / safe_name
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if not target_path.resolve().is_relative_to(Path(INPUT_DIR).resolve()):
        raise ValueError("Invalid upload path")
    return target_path


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Save an uploaded file to the local uploads directory using a safe name."""

    file_path = _safe_path(file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"message": "File uploaded successfully", "filename": file_path.name}