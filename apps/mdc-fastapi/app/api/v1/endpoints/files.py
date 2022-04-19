from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, Response
from fastapi.encoders import jsonable_encoder

from app import schemas, utils
from app.api import deps

router = APIRouter()


@router.get("/", response_model=List[schemas.FileInfo])
def read_uploads(
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve uploaded files.
    """
    return []


@router.post("/", response_model=schemas.FileInfo)
async def create_upload(
    *,
    file: UploadFile,
) -> Any:
    """
    Upload a file.
    """
    fileinfo = await utils.file.save(file)
    return fileinfo


@router.get("/{id}")
def read_upload(*, id: str):
    """
    Get an uploaded file by ID.
    """
    try:
        fileinfo = utils.file.retrieve_by_id(id)
    except FileNotFoundError:
        return HTTPException(status_code=404)
    with fileinfo.filepath.open('rb') as f:
        data = f.read()
    return Response(content=data, media_type=utils.file.get_mime_type(fileinfo.filepath))
