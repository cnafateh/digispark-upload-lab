from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse

APP_TITLE = os.getenv("APP_TITLE", "Digispark Upload Lab")
API_KEY = os.getenv("UPLOAD_API_KEY", "change-me")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "/data/uploads"))
ALLOWED_EXTENSIONS = {
    ext.strip().lower()
    for ext in os.getenv("ALLOWED_EXTENSIONS", ".txt").split(",")
    if ext.strip()
}

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title=APP_TITLE,
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)


def safe_filename(filename: str | None) -> str:
    if not filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    cleaned = Path(filename).name.strip()
    if not cleaned or cleaned in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename")

    suffix = Path(cleaned).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {allowed}",
        )

    return cleaned


async def persist_upload(upload: UploadFile) -> tuple[str, int]:
    filename = safe_filename(upload.filename)
    destination = UPLOAD_DIR / filename
    temp_destination = UPLOAD_DIR / f".{filename}.uploading"

    size = 0
    try:
        with temp_destination.open("wb") as output:
            while chunk := await upload.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File exceeds {MAX_FILE_SIZE_MB} MB limit",
                    )
                output.write(chunk)

        temp_destination.replace(destination)
    except Exception:
        temp_destination.unlink(missing_ok=True)
        raise
    finally:
        await upload.close()

    return filename, size


def file_items() -> list[dict]:
    items = []
    for path in sorted(
        (p for p in UPLOAD_DIR.iterdir() if p.is_file() and not p.name.startswith(".")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    ):
        stat = path.stat()
        items.append(
            {
                "name": path.name,
                "size": stat.st_size,
                "size_human": human_size(stat.st_size),
                "modified": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).strftime("%Y-%m-%d %H:%M UTC"),
            }
        )
    return items


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "service": APP_TITLE,
        "allowed_extensions": sorted(ALLOWED_EXTENSIONS),
        "max_file_size_mb": MAX_FILE_SIZE_MB,
    }


@app.post("/api/upload")
async def api_upload(
    file: Annotated[UploadFile, File(...)],
    x_api_key: Annotated[str | None, Header()] = None,
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    filename, size = await persist_upload(file)
    return {
        "success": True,
        "filename": filename,
        "size": size,
        "size_human": human_size(size),
    }


@app.get("/files/{filename}")
def download_file(filename: str):
    cleaned = safe_filename(filename)
    path = UPLOAD_DIR / cleaned

    if not path.is_file():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=path,
        filename=cleaned,
        media_type="text/plain",
    )
