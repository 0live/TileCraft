from typing import Annotated

from app.core.security import get_current_user
from app.modules.import_data.service import ImportService
from app.modules.users.models import User
from fastapi import APIRouter, Depends, File, Form, UploadFile, status

router = APIRouter()


@router.post("/import", status_code=status.HTTP_202_ACCEPTED)
async def import_data(
    file: Annotated[UploadFile, File(...)],
    table_name: Annotated[str, Form(...)],
    schema: Annotated[str, Form(...)] = "geodata",
    current_user: User = Depends(get_current_user),
):
    """
    Upload a geospatial file and trigger an async import task.
    """
    return await ImportService.create_import_task(file, schema, table_name)
