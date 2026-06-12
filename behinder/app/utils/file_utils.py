"""
文件处理工具
"""
import os
import uuid
import aiofiles
from pathlib import Path
from fastapi import UploadFile

# 项目根目录（behinder/app/utils/file_utils.py → parent×4 = 项目根目录）
_PROJ_ROOT = Path(__file__).resolve().parent.parent.parent.parent
UPLOAD_DIR = _PROJ_ROOT / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


def validate_file_extension(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


async def save_upload_file(file: UploadFile) -> str:
    """保存上传文件，返回文件路径"""
    ext = Path(file.filename).suffix.lower()
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / unique_name

    async with aiofiles.open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    return str(file_path)
