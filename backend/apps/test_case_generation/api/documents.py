import os
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.ui_automation.database import get_db
from apps.ui_automation.api.auth import get_current_user
from ..repositories.file_repo import FileRepository
from ..schemas import FileOut, ApiResponse

router = APIRouter(tags=["TCG-文件管理"])

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "data", "tcg_uploads"))
ALLOWED_TYPES = {".pdf", ".docx", ".doc", ".txt", ".md", ".png", ".jpg", ".jpeg", ".xlsx", ".xls"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/files/upload")
async def upload_file(
    project_id: str = Query(...),
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_TYPES:
        return ApiResponse(success=False, message=f"不支持的文件类型: {ext}")

    content = await file.read()
    if len(content) == 0:
        return ApiResponse(success=False, message="文件内容为空（0 字节），请检查文件是否正确")
    if len(content) > MAX_FILE_SIZE:
        return ApiResponse(success=False, message="文件大小超过 50MB 限制")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    save_path = os.path.join(UPLOAD_DIR, f"{file_id}{ext}")
    with open(save_path, "wb") as f:
        f.write(content)

    repo = FileRepository(db)
    record = await repo.create(
        id=file_id,
        project_id=project_id,
        file_name=file.filename,
        file_type=ext.lstrip("."),
        file_path=save_path,
        file_size=len(content),
    )

    return ApiResponse(data=FileOut.model_validate(record))


@router.get("/files")
async def list_files(
    project_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = FileRepository(db)
    files = await repo.list_by_project(project_id)
    return ApiResponse(data=[FileOut.model_validate(f) for f in files])


@router.delete("/files/{file_id}")
async def delete_file(
    file_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = FileRepository(db)
    f = await repo.get_by_id(file_id)
    if not f:
        return ApiResponse(success=False, message="文件不存在")
    if f.file_path and os.path.exists(f.file_path):
        os.remove(f.file_path)
    await repo.delete(file_id)
    return ApiResponse(message="删除成功")
