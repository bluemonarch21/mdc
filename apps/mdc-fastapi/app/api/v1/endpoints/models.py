from typing import Any, List

from fastapi import APIRouter

from app import schemas, utils

router = APIRouter()


@router.get("/", response_model=List[schemas.ModelInfo])
def read_models() -> Any:
    """
    Retrieve models information.
    """
    return utils.model.info()
