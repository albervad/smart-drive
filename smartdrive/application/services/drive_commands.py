import asyncio
import os
from urllib.parse import unquote

from fastapi import HTTPException

from smartdrive.infrastructure.clipboard_store import save_shared_clipboard
from smartdrive.infrastructure.file_ops import (
    build_zip_archive,
    create_directory,
    delete_empty_directory,
    delete_file,
    ensure_directory,
    is_dir,
    is_file,
    move_file_sync,
    path_exists,
    rename_path,
)
from smartdrive.infrastructure.settings import FILES_DIR, INBOX_DIR
from smartdrive.infrastructure.storage import (
    generate_unique_name,
    sanitize_input_path,
)
from smartdrive.presentation.schemas import MoveSchema, RenameSchema


def _get_base_dir_for_zone(zone: str) -> str:
    if zone == "inbox":
        return INBOX_DIR
    if zone == "catalog":
        return FILES_DIR
    raise HTTPException(status_code=400, detail="Zona de borrado invalida")


def delete_item(zone: str, filepath: str) -> dict:
    try:
        path = sanitize_input_path(unquote(filepath), _get_base_dir_for_zone(zone))

        if path_exists(path) and is_file(path):
            delete_file(path)
            return {"info": f"Archivo eliminado de {zone}"}

        raise HTTPException(status_code=404, detail="El archivo no existe")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al borrar: {str(exc)}")


def create_folder(folder_name: str) -> dict:
    try:
        new_path = sanitize_input_path(folder_name, FILES_DIR)
        if not path_exists(new_path):
            create_directory(new_path)
            return {"info": "Carpeta creada"}
        return {"error": "La carpeta ya existe"}
    except Exception as exc:
        return {"error": str(exc)}


async def move_file(data: MoveSchema) -> dict:
    try:
        source_input = unquote(data.source_path)
        destination_input = unquote(data.destination_folder)

        if data.source_zone == "inbox":
            source_path = sanitize_input_path(source_input, INBOX_DIR)
        elif data.source_zone == "catalog":
            source_path = sanitize_input_path(source_input, FILES_DIR)
        else:
            return {"error": "Zona de origen desconocida"}

        if not is_file(source_path):
            return {"error": f"El archivo origen no existe en {data.source_zone}"}

        if destination_input == ".":
            destination_folder = FILES_DIR
        else:
            destination_folder = sanitize_input_path(destination_input, FILES_DIR)

        if not path_exists(destination_folder):
            ensure_directory(destination_folder)

        filename = os.path.basename(source_path)
        destination_path = os.path.join(destination_folder, filename)

        if path_exists(destination_path):
            return {"error": "El archivo ya existe en la carpeta destino"}

        await asyncio.to_thread(move_file_sync, source_path, destination_path)
        return {"info": f"Movido a {destination_input}"}
    except Exception as exc:
        return {"error": f"Error al mover: {str(exc)}"}


def rename_item(data: RenameSchema) -> dict:
    try:
        if data.zone not in ["catalog", "folder"]:
            raise HTTPException(status_code=400, detail="Zona invalida")

        clean_path = unquote(data.item_path).strip()
        new_name = data.new_name.strip()

        if not new_name:
            raise HTTPException(status_code=400, detail="El nuevo nombre es obligatorio")

        if "/" in new_name or "\\" in new_name:
            raise HTTPException(status_code=400, detail="Nombre invalido")

        source_path = sanitize_input_path(clean_path, FILES_DIR)

        if not path_exists(source_path):
            raise HTTPException(status_code=404, detail="Elemento no encontrado")

        if data.zone == "folder" and not is_dir(source_path):
            raise HTTPException(status_code=400, detail="La ruta no es una carpeta")

        if data.zone == "catalog" and not is_file(source_path):
            raise HTTPException(status_code=400, detail="La ruta no es un archivo")

        parent_dir = os.path.dirname(source_path)
        target_path = os.path.join(parent_dir, new_name)
        target_rel = os.path.relpath(target_path, FILES_DIR)
        safe_target = sanitize_input_path(target_rel, FILES_DIR)

        if path_exists(safe_target):
            raise HTTPException(status_code=409, detail="Ya existe un elemento con ese nombre")

        rename_path(source_path, safe_target)
        new_relative = os.path.relpath(safe_target, FILES_DIR).replace("\\", "/")
        return {"info": "Renombrado correctamente", "new_path": new_relative}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error al renombrar: {str(exc)}")


def save_clipboard(text: str) -> dict:
    try:
        return save_shared_clipboard(text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No se pudo guardar el portapapeles: {str(exc)}")


def delete_folder(path: str) -> dict:
    try:
        full_path = sanitize_input_path(unquote(path), FILES_DIR)

        if full_path == FILES_DIR:
            raise HTTPException(status_code=403, detail="No se puede borrar la raiz")

        if path_exists(full_path) and is_dir(full_path):
            try:
                delete_empty_directory(full_path)
                return {"info": "Carpeta eliminada"}
            except OSError:
                raise HTTPException(status_code=409, detail="La carpeta NO esta vacia.")

        raise HTTPException(status_code=404, detail="Carpeta no encontrada")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error: {str(exc)}")


def prepare_folder_zip(path: str) -> tuple[str, str]:
    full_path = sanitize_input_path(unquote(path), FILES_DIR)

    if not is_dir(full_path):
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")

    return build_zip_archive(full_path)
