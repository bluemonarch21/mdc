from typing import List

from pydantic import BaseModel


class Prediction(BaseModel):
    model: str
    input: str
    label: int
