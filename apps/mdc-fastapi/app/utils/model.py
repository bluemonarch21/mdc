import asyncio
from typing import List

from pycaret.classification import load_model, predict_model as predict_cls_model
from pycaret.regression import predict_model as predict_reg_model
from music21 import features, converter
import pandas as pd

from app import schemas
from app.core.config import settings


def info() -> List[schemas.ModelInfo]:
    out = []
    for model_path in (settings.DATA_DIR / "models").glob("*.pkl"):
        parts = []
        if "rf" in model_path.name:
            parts.append("Random Forest")
        elif "et" in model_path.name:
            parts.append("Extra Trees")
        elif "xgb" in model_path.name:
            parts.append("Extreme Gradient Boosting")
        elif "catboost" in model_path.name:
            parts.append("CatBoost")
        if "reg" in model_path.name:
            parts.append("Regressor")
        else:
            parts.append("Classifier")
        if "v1" in model_path.name:
            parts.append("v1")
        out.append(schemas.ModelInfo(id=model_path.stem, description=" ".join(parts)))
    return out


_models = dict()
feature_extractors = []


async def load_feature_extractors():
    global feature_extractors
    feature_extractors = features.extractorsById([
        'r31',  # music21.features.jSymbolic.InitialTimeSignatureFeature
        'r32',  # music21.features.jSymbolic.CompoundOrSimpleMeterFeature
        'r33',  # music21.features.jSymbolic.TripleMeterFeature
        'r34',  # music21.features.jSymbolic.QuintupleMeterFeature
        'r35',  # music21.features.jSymbolic.ChangesOfMeterFeature
        'p1',   # music21.features.jSymbolic.MostCommonPitchPrevalenceFeature
        'p2',   # music21.features.jSymbolic.MostCommonPitchClassPrevalenceFeature
        'p3',   # music21.features.jSymbolic.RelativeStrengthOfTopPitchesFeature
        'p4',   # music21.features.jSymbolic.RelativeStrengthOfTopPitchClassesFeature
        'p5',   # music21.features.jSymbolic.IntervalBetweenStrongestPitchesFeature`
        'p6',   # music21.features.jSymbolic.IntervalBetweenStrongestPitchClassesFeature
        'p7',   # music21.features.jSymbolic.NumberOfCommonPitchesFeature
        'p8',   # music21.features.jSymbolic.PitchVarietyFeature
        'p9',   # music21.features.jSymbolic.PitchClassVarietyFeature
        'p10',  # music21.features.jSymbolic.RangeFeature
        'p11',  # music21.features.jSymbolic.MostCommonPitchFeature
        'p12',  # music21.features.jSymbolic.PrimaryRegisterFeature
        'p13',  # music21.features.jSymbolic.ImportanceOfBassRegisterFeature
        'p14',  # music21.features.jSymbolic.ImportanceOfMiddleRegisterFeature
        'p15',  # music21.features.jSymbolic.ImportanceOfHighRegisterFeature
        'p16',  # music21.features.jSymbolic.MostCommonPitchClassFeature
        'p19',  # music21.features.jSymbolic.BasicPitchHistogramFeature
        'p20',  # music21.features.jSymbolic.PitchClassDistributionFeature
        'p21',  # music21.features.jSymbolic.FifthsPitchHistogramFeature
    ])


_task = asyncio.create_task(load_feature_extractors())


async def get_feature_extractors():
    await _task
    return feature_extractors


async def get_model(model_name: str):
    if model_name in _models:
        return _models[model_name]
    else:
        try:
            model = load_model(str(settings.DATA_DIR / "models" / model_name))
            _models[model_name] = model
        except ValueError:
            # sometimes it errors, trying again works somehow
            raise
        except Exception as e:
            raise e


async def extract_features(fileinfo: schemas.FileInfo) -> pd.DataFrame:
    ds = features.DataSet(classLabel='ClassLabel')
    ds.addFeatureExtractors(await get_feature_extractors())
    s = converter.parse(str(fileinfo.filepath))
    ds.addData(s)
    ds.process()
    df = pd.DataFrame(ds.getFeaturesAsList(), columns=ds.getAttributeLabels())
    return df


async def predict(model_name: str, fileinfo: schemas.FileInfo) -> schemas.Prediction:
    task1 = asyncio.create_task(extract_features(fileinfo))
    task2 = asyncio.create_task(get_model(model_name))
    # model = load_model(str(settings.DATA_DIR / "models" / model_name))
    await asyncio.gather(task1, task2)
    if "reg" in fileinfo.filename:
        predictions = predict_reg_model(task2.result(), data=task1.result())
    else:
        predictions = predict_cls_model(task2.result(), data=task1.result())
    label = predictions.loc[0]['Label']
    score = predictions.loc[0]['Score']
    return schemas.Prediction(model=model_name, input=fileinfo.filename, label=label, score=score)
