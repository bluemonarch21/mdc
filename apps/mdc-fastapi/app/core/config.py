import os
import pathlib
from pathlib import Path
from typing import List, Union

from pydantic import AnyHttpUrl, BaseSettings, validator

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    SERVER_NAME: str = ""
    SERVER_HOST: AnyHttpUrl = "http://localhost:8080"
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    # e.g: '["http://localhost", "http://localhost:4200", "http://localhost:3000", "http://localhost:8080"]'
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    PROJECT_NAME: str
    DATA_PATH: str = "data"
    UPLOAD_PATH: str = "userupload"

    @property
    def DATA_DIR(self) -> pathlib.Path:
        path = BASE_DIR / self.DATA_PATH
        if not path.is_dir() and path.exists():
            os.remove(path)
        if not path.exists():
            os.mkdir(path)
        return path

    @property
    def UPLOAD_DIR(self) -> pathlib.Path:
        path = self.DATA_DIR / self.UPLOAD_PATH
        if not path.is_dir() and path.exists():
            os.remove(path)
        if not path.exists():
            os.mkdir(path)
        return path

    class Config:
        case_sensitive = True


settings = Settings(_env_file=BASE_DIR / ".env", _env_file_encoding="utf-8")
