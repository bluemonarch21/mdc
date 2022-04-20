from typing import Any

from fastapi import APIRouter, HTTPException

from app import schemas, utils
from app.api import deps

router = APIRouter()


@router.get("/", response_model=schemas.Prediction)
async def read_prediction(
    *,
    model: str,
    id: str,
) -> Any:
    """
    Retrieve prediction of an uploaded file.
    """
    try:
        fileinfo = utils.file.retrieve_by_id(id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    if fileinfo.filepath.suffix != ".mxl":
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {fileinfo.filepath.suffix}")
    try:
        prediction = await utils.model.predict(model, fileinfo)
    except ValueError:
        raise HTTPException(status_code=503, headers={"Retry-After": "2"})
    return prediction
