import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import Column, String, DateTime, select

from db import db

path = os.getenv(
    "UPLOAD_FILE_PATH",
    os.path.join(os.getcwd(), "uploads")
)


class FileModel(db.Model):
    id = Column(String(), primary_key=True)
    filename = Column(String(), nullable=False)
    path = Column(String(), nullable=False)
    created_at = Column(DateTime(), default=datetime.utcnow, nullable=False)

    @staticmethod
    def store_file(file, commit=True):
        file_id = str(uuid.uuid4())
        file_extension = "".join(Path(file.filename).suffixes)
        original_file_name = file.filename
        new_file_name = f"{file_id}{file_extension}"
        file_path = os.path.join(path, new_file_name)

        try:
            file.save(file_path)
            file_model = FileModel(
                id=file_id,
                filename=original_file_name,
                path=file_path,
            )
            db.session.add(file_model)
            db.session.flush()
            if commit:
                db.session.commit()
            return file_model
        except Exception:
            if os.path.exists(file_path):
                os.remove(file_path)
            raise

    @staticmethod
    def remove_file(file_to_delete_id, commit=True):
        file_model: Optional[FileModel] = db.session.execute(
            select(FileModel).where(FileModel.id == file_to_delete_id).limit(1)
        ).scalar()
        if file_model:
            if os.path.exists(file_model.path):
                # os.remove(file_model.path)
                pass
            db.session.delete(file_model)
            if commit:
                db.session.commit()
