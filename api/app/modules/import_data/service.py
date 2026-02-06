import os
import shutil
import uuid

from app.modules.import_data.tasks import import_file_task
from fastapi import UploadFile

UPLOAD_DIR = "/tmp/imports"  # Shared volume or temp dir


class ImportService:
    @staticmethod
    async def create_import_task(file: UploadFile, schema: str, table_name: str):
        if not os.path.exists(UPLOAD_DIR):
            os.makedirs(UPLOAD_DIR)

        # Save file
        file_ext = os.path.splitext(file.filename)[1]
        file_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}{file_ext}")

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Trigger Celery Task
        task = import_file_task.delay(file_path, schema, table_name)

        return {"task_id": task.id, "status": "processing"}
