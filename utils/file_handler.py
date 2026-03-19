import os
from fastapi import UploadFile


async def save_upload(file: UploadFile, path: str) -> None:
    """Save uploaded file to disk."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)


def cleanup_input(path: str) -> None:
    """Delete input file after processing."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass