import os
import pathlib
import secrets
import typing
from typing import Generator

import pandas as pd
from fastapi import UploadFile

from app import schemas
from app.core.config import settings


async def save(file: UploadFile) -> schemas.FileInfo:
    while True:
        id_ = secrets.token_hex(8)
        fileinfo = schemas.FileInfo(id=id_, filename=file.filename)
        try:
            retrieve_by_id(id_)
            continue
        except FileNotFoundError:
            with fileinfo.filepath.open("wb") as f:
                contents = await file.read()
                f.write(contents)
            return fileinfo


def retrieve_by_id(id: str) -> schemas.FileInfo:
    search_path = settings.DATA_DIR / "userupload"
    for path in search_path.glob(f"{id}_*"):
        _, filename = path.name.split("_", 1)
        return schemas.FileInfo(id=id, filename=filename)
    raise FileNotFoundError


def retrieve_by_name(filename: str) -> Generator[schemas.FileInfo, typing.Any, None]:
    search_path = settings.DATA_DIR / "userupload"
    for path in search_path.glob(f"*_{filename}"):
        _, filename = path.name.split("_", 1)
        yield schemas.FileInfo(id=id, filename=filename)
    return


def clean():
    search_path = settings.DATA_DIR / "userupload"
    for path in search_path.glob("*"):
        yield os.remove(path)


common_mime = pd.read_csv(pathlib.Path(__file__).resolve().parent / "common-mime-types.csv")


def get_mime_type(filepath: pathlib.Path) -> str:
    ext = filepath.suffix.lower()
    return next(common_mime[common_mime['Extension'] == ext].iterrows())[1]['MIME Type']
