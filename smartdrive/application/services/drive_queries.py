from fastapi import HTTPException

from smartdrive.domain.folder_rules import suggest_folder_by_extension
from smartdrive.infrastructure.clipboard_store import read_shared_clipboard
from smartdrive.infrastructure.search import search_files
from smartdrive.infrastructure.settings import FILES_DIR
from smartdrive.infrastructure.storage import (
    build_recursive_tree,
    get_disk_usage,
    list_flat_folders,
    list_inbox_files,
)


def get_drive_home_context() -> dict:
    used, free, percent = get_disk_usage()
    tree = build_recursive_tree(FILES_DIR)
    return {
        "used_space": used,
        "free_space": free,
        "usage_percent": percent,
        "inbox_files": list_inbox_files(),
        "file_tree": tree["subfolders"],
    }


def search_drive_files(q: str = "", mode: str = "both") -> dict:
    query = q.strip()
    search_mode = mode.strip().lower()

    if search_mode not in {"both", "name", "content"}:
        raise HTTPException(status_code=400, detail="Modo de busqueda invalido")
    if len(query) > 120:
        raise HTTPException(status_code=400, detail="Consulta demasiado larga")
    if len(query) < 2:
        return {"results": [], "total": 0}

    results = search_files(query, mode=search_mode)
    return {"results": results, "total": len(results)}


def list_all_folders() -> dict:
    return {"folders": list_flat_folders(FILES_DIR)}


def scan_folders(filename: str) -> dict:
    return {
        "folders": list_flat_folders(FILES_DIR),
        "suggested": suggest_folder_by_extension(filename),
    }


def get_shared_clipboard() -> dict:
    return read_shared_clipboard()


def get_tree_context() -> dict:
    tree = build_recursive_tree(FILES_DIR)
    return {"file_tree": tree["subfolders"]}
