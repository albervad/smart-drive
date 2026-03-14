from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from smartdrive.infrastructure.runtime import app_lifespan
from smartdrive.infrastructure.settings import INBOX_DIR, FILES_DIR
from smartdrive.presentation.routers.drive_router import router as drive_router
from smartdrive.presentation.routers.portfolio_router import router as portfolio_router


def create_app() -> FastAPI:
    app = FastAPI(
        lifespan=app_lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    app.mount("/drive/inbox", StaticFiles(directory=INBOX_DIR, check_dir=False), name="drive-inbox")
    app.mount("/drive/files", StaticFiles(directory=FILES_DIR, check_dir=False), name="drive-files")
    app.mount("/static", StaticFiles(directory="static"), name="static")

    app.include_router(portfolio_router)
    app.include_router(drive_router)
    return app
