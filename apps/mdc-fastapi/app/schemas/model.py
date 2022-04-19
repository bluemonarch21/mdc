from pydantic import BaseModel


class ModelInfo(BaseModel):
    id: str
    description: str
