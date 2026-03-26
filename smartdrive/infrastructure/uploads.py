import shutil

from fastapi import UploadFile


def write_upload_chunk(file: UploadFile, partial_path: str) -> None:
    with open(partial_path, "ab", buffering=16 * 1024 * 1024) as file_handle:
        shutil.copyfileobj(file.file, file_handle, length=16 * 1024 * 1024)
