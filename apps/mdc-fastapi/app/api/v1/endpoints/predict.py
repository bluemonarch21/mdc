from typing import Any

from fastapi import APIRouter

from app import schemas, utils
from app.api import deps

router = APIRouter()


@router.get("/", response_model=schemas.Prediction)
def read_prediction(
    *,
    model: str,
    id: str,
) -> Any:
    """
    Retrieve prediction of an uploaded file.
    """
    fileinfo = utils.file.retrieve_by_id(id)
    return utils.model.predict(model, fileinfo)
