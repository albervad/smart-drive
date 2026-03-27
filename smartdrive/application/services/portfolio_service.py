import json
import os

from smartdrive.domain.writeups import normalize_writeups_data
from smartdrive.infrastructure.settings import WRITEUPS_MAX_FILE_BYTES


def get_portfolio_writeups() -> list[dict]:
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    writeups_path = os.path.join(project_root, "static", "data", "writeups.json")
    writeups_data = []

    try:
        if os.path.getsize(writeups_path) > WRITEUPS_MAX_FILE_BYTES:
            raise ValueError("writeups.json demasiado grande")

        with open(writeups_path, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
            writeups_data = normalize_writeups_data(data)
    except Exception:
        writeups_data = []

    return writeups_data
