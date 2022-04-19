import pathlib
from typing import List

from app import schemas


def info() -> List[schemas.ModelInfo]:
    return [schemas.ModelInfo(id=id, description=description) for id, description in (
        ('catboost512', 'CatBoost + 512 henle-music21 dataset'),
        ('rf512', 'Random Forest + 512 henle-music21 dataset'),
    )]


def predict(model: str, fileinfo: schemas.FileInfo) -> schemas.Prediction:
    label = 4
    return schemas.Prediction(model=model, input=fileinfo.filename, label=label)
