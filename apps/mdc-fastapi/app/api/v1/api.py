from fastapi import APIRouter

from app.api.v1.endpoints import files, models, predict

api_router = APIRouter()
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(predict.router, prefix="/predict", tags=["predict"])
