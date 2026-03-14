from fastapi import APIRouter, Request, File, UploadFile, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse

from smartdrive.application.services.drive_commands import (
    create_folder as create_folder_command,
    delete_folder as delete_folder_command,
    delete_item as delete_item_command,
    move_file as move_file_command,
    prepare_folder_zip as prepare_folder_zip_command,
    rename_item as rename_item_command,
    save_clipboard as save_clipboard_command,
)
from smartdrive.application.services.drive_queries import (
    get_drive_home_context as get_drive_home_context_query,
    get_shared_clipboard as get_shared_clipboard_query,
    get_tree_context as get_tree_context_query,
    list_all_folders as list_all_folders_query,
    scan_folders as scan_folders_query,
    search_drive_files as search_drive_files_query,
)
from smartdrive.application.services.drive_uploads import (
    finish_upload as finish_upload_command,
    get_upload_status as get_upload_status_query,
    upload_chunk as upload_chunk_command,
)
from smartdrive.infrastructure.file_ops import safe_remove_file
from smartdrive.infrastructure.templates import templates
from smartdrive.presentation.schemas import FolderSchema, MoveSchema, ClipboardSchema, RenameSchema


router = APIRouter(prefix="/drive")


@router.get("/")
def drive_home(request: Request):
    context = get_drive_home_context_query()
    context["request"] = request
    return templates.TemplateResponse("index.html", context)


@router.get("/search")
def search_files(q: str = "", mode: str = "both"):
    return search_drive_files_query(q=q, mode=mode)


@router.delete("/delete/{zone}/{filepath:path}")
def delete_item(zone: str, filepath: str):
    return delete_item_command(zone, filepath)


@router.get("/upload_status")
def get_upload_status(filename: str):
    return get_upload_status_query(filename)


@router.post("/upload_chunk")
def upload_chunk(
    file: UploadFile = File(...),
    filename: str = Form(...),
    chunk_offset: int = Form(...),
):
    return upload_chunk_command(file=file, filename=filename, chunk_offset=chunk_offset)


@router.post("/upload_finish")
def finish_upload(
    filename: str = Form(...),
    action: str = Form("check"),
):
    return finish_upload_command(filename=filename, action=action)


@router.post("/create-folder")
def create_folder(folder: FolderSchema):
    return create_folder_command(folder.folder_name)


@router.get("/all-folders")
def get_all_folders():
    return list_all_folders_query()


@router.get("/scan-folders/{filename}")
def scan_folders(filename: str):
    return scan_folders_query(filename)


@router.post("/move")
async def move_file(data: MoveSchema):
    return await move_file_command(data)


@router.post("/rename")
def rename_item(data: RenameSchema):
    return rename_item_command(data)


@router.get("/clipboard")
def get_shared_clipboard():
    return get_shared_clipboard_query()


@router.post("/clipboard")
def set_shared_clipboard(payload: ClipboardSchema):
    return save_clipboard_command(payload.text)


@router.delete("/delete-folder/{path:path}")
def delete_folder(path: str):
    return delete_folder_command(path)


@router.get("/download-folder/{path:path}")
def download_folder_zip(path: str, background_tasks: BackgroundTasks):
    try:
        zip_path, zip_filename = prepare_folder_zip_command(path)
        background_tasks.add_task(safe_remove_file, zip_path)
        return FileResponse(zip_path, media_type="application/zip", filename=zip_filename)
    except Exception as exc:
        print(f"Error ZIP: {exc}")
        raise HTTPException(status_code=500, detail="Error creando ZIP")


@router.get("/tree-html")
def get_tree_html(request: Request):
    context = get_tree_context_query()
    context["request"] = request
    return templates.TemplateResponse("tree_fragment.html", context)
