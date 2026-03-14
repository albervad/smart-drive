import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from smartdrive.infrastructure.settings import INBOX_DIR, FILES_DIR


def ensure_storage_folders() -> None:
    storage_paths = [INBOX_DIR, FILES_DIR]
    print("--> Iniciando Smart Drive. Verificando rutas...")

    for storage_path in storage_paths:
        if not os.path.exists(storage_path):
            try:
                os.makedirs(storage_path, exist_ok=True)
                print(f"    [OK] Creada carpeta: {storage_path}")
            except PermissionError:
                print(f"    [ERROR] Sin permisos para crear: {storage_path}")
        else:
            print(f"    [OK] Detectada: {storage_path}")


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    ensure_storage_folders()
    yield
    print("--> Apagando Smart Drive...")
