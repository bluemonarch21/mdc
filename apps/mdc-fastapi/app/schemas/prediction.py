from typing import Optional

from pydantic import BaseModel


class Prediction(BaseModel):
    model: str
    input: str
    label: int
    score: Optional[float] = None
