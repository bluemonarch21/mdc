import pathlib

from pydantic import BaseModel

from app.core.config import settings


class FileInfo(BaseModel):
    id: str
    filename: str

    @property
    def filepath(self) -> pathlib.Path:
        return settings.UPLOAD_DIR / f"{self.id}_{self.filename}"
