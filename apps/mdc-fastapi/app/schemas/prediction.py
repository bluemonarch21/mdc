from typing import Optional, Union

from pydantic import BaseModel


class Prediction(BaseModel):
    model: str
    input: str
    label: Union[int, float]
    score: Optional[float] = None
