from fastapi import HTTPException

from smartdrive.domain.folder_rules import suggest_folder_by_extension
from smartdrive.infrastructure.clipboard_store import read_shared_clipboard
from smartdrive.infrastructure.logging import get_logger
from smartdrive.infrastructure.search import search_files
from smartdrive.infrastructure.settings import FILES_DIR
from smartdrive.infrastructure.storage import (
    build_recursive_tree,
    get_disk_usage,
    list_flat_folders,
    list_inbox_files,
)


logger = get_logger("drive_queries")


def _count_tree_entries(nodes: list[dict]) -> tuple[int, int]:
    folder_count = len(nodes)
    file_count = 0

    for folder in nodes:
        file_count += len(folder.get("files", []))
        nested_folders, nested_files = _count_tree_entries(folder.get("subfolders", []))
        folder_count += nested_folders
        file_count += nested_files

    return folder_count, file_count


def get_drive_home_context() -> dict:
    logger.debug("Building drive home context")
    used, free, percent = get_disk_usage()
    tree = build_recursive_tree(FILES_DIR)
    subfolders = tree["subfolders"]
    folder_count, file_count = _count_tree_entries(subfolders)
    inbox_files = list_inbox_files()

    logger.debug(
        "Drive home context ready. inbox_files=%s catalog_folders=%s catalog_files=%s usage_percent=%s",
        len(inbox_files),
        folder_count,
        file_count,
        percent,
    )

    return {
        "used_space": used,
        "free_space": free,
        "usage_percent": percent,
        "inbox_files": inbox_files,
        "file_tree": subfolders,
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
    folders = list_flat_folders(FILES_DIR)
    logger.debug("Folder listing ready. folders=%s", len(folders))
    return {"folders": folders}


def scan_folders(filename: str) -> dict:
    logger.debug("Scanning folders for file suggestion. filename=%s", filename)
    folders = list_flat_folders(FILES_DIR)
    suggested = suggest_folder_by_extension(filename)
    logger.debug(
        "Folder scan ready. filename=%s folders=%s suggested=%s",
        filename,
        len(folders),
        suggested,
    )
    return {
        "folders": folders,
        "suggested": suggested,
    }


def get_shared_clipboard() -> dict:
    return read_shared_clipboard()


def get_tree_context() -> dict:
    logger.debug("Building tree context")
    tree = build_recursive_tree(FILES_DIR)
    subfolders = tree["subfolders"]
    folder_count, file_count = _count_tree_entries(subfolders)
    logger.debug(
        "Tree context ready. catalog_folders=%s catalog_files=%s",
        folder_count,
        file_count,
    )
    return {"file_tree": subfolders}
