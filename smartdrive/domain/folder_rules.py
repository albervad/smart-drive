IMAGE_EXTENSIONS = {"jpg", "png", "jpeg", "gif", "webp", "svg"}
DOCUMENT_EXTENSIONS = {"pdf", "doc", "docx", "txt", "xls", "xlsx"}
VIDEO_EXTENSIONS = {"mp4", "mkv", "avi", "mov"}
CODE_EXTENSIONS = {"py", "js", "html", "css", "json"}


def suggest_folder_by_extension(filename: str) -> str:
    extension = filename.split(".")[-1].lower() if "." in filename else ""

    if extension in IMAGE_EXTENSIONS:
        return "Imagenes"
    if extension in DOCUMENT_EXTENSIONS:
        return "Documentos"
    if extension in VIDEO_EXTENSIONS:
        return "Videos"
    if extension in CODE_EXTENSIONS:
        return "Programacion"

    return "."
