import logging
import tempfile

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile, status, Request
from src.domain import commands
from src.bootstrap import bootstrap

logger = logging.getLogger(__name__)

router = APIRouter()


def get_bus(request: Request):
    from src.bootstrap import get_message_bus
    return get_message_bus()

CHUNK_SIZE = 1024 * 1024

@router.post("/api/upload", status_code=201)
async def upload_file(file: UploadFile, request: Request):
    bus = get_bus(request)
    try:
        with tempfile.NamedTemporaryFile() as temp_file:
            filename = temp_file.name
            logger.info(f"Saving uploaded file temporarily to {filename}")
            async with aiofiles.open(filename, "wb") as f:
                while chunk := await file.read(CHUNK_SIZE):
                    await f.write(chunk)

            cmd = commands.UploadFile(file_name=file.filename, local_path=filename)
            [file_url] = bus.handle(cmd)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error uploading the file",
        )

    return {"detail": f"Successfully uploaded {file.filename}", "file_url": file_url}
