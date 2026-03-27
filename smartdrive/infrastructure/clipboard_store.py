import json
import os
from datetime import datetime, timezone

from smartdrive.domain.writeups import sanitize_text
from smartdrive.infrastructure.settings import (
    BASE_MOUNT,
    CLIPBOARD_MAX_FILE_BYTES,
    CLIPBOARD_MAX_TEXT_CHARS,
)


def get_shared_clipboard_path() -> str:
    if os.path.exists(BASE_MOUNT):
        return os.path.join(BASE_MOUNT, ".clipboard_shared.json")
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(project_root, "static", "data", "clipboard.json")


def normalize_clipboard_text(value) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    value = value.replace("\x00", "")
    if len(value) > CLIPBOARD_MAX_TEXT_CHARS:
        return value[:CLIPBOARD_MAX_TEXT_CHARS]
    return value


def read_shared_clipboard() -> dict:
    path = get_shared_clipboard_path()
    default_payload = {"text": "", "updated_at": None}

    if not os.path.exists(path):
        return default_payload

    try:
        if os.path.getsize(path) > CLIPBOARD_MAX_FILE_BYTES:
            return default_payload

        with open(path, "r", encoding="utf-8") as file_handle:
            raw = json.load(file_handle)

        if not isinstance(raw, dict):
            return default_payload

        return {
            "text": normalize_clipboard_text(raw.get("text", "")),
            "updated_at": sanitize_text(raw.get("updated_at"), 80) or None,
        }
    except Exception:
        return default_payload


def save_shared_clipboard(text: str) -> dict:
    path = get_shared_clipboard_path()
    payload = {
        "text": normalize_clipboard_text(text),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as file_handle:
        json.dump(payload, file_handle, ensure_ascii=False)

    return payload
