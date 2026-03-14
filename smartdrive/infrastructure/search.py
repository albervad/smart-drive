import html
import os
import re
import zipfile
from urllib.parse import quote

from smartdrive.infrastructure.settings import (
    CONTENT_SEARCH_EXTENSIONS,
    FILES_DIR,
    INBOX_DIR,
    MAX_CONTENT_SEARCH_BYTES,
    MAX_EXTRACT_CHARS,
    MAX_SEARCH_RESULTS,
)
from smartdrive.infrastructure.storage import format_size


def is_path_within_base(path: str, base_dir: str) -> bool:
    try:
        base_real = os.path.realpath(base_dir)
        file_real = os.path.realpath(path)
        return os.path.commonpath([file_real, base_real]) == base_real
    except Exception:
        return False


def is_content_searchable(file_path: str) -> bool:
    extension = os.path.splitext(file_path)[1].lower()
    if extension not in CONTENT_SEARCH_EXTENSIONS:
        return False
    try:
        return os.path.getsize(file_path) <= MAX_CONTENT_SEARCH_BYTES
    except OSError:
        return False


def extract_plain_text(file_path: str) -> str:
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as file_handle:
            return file_handle.read(MAX_EXTRACT_CHARS)
    except Exception:
        return ""


def extract_pdf_text(file_path: str) -> str:
    try:
        from pypdf import PdfReader
    except Exception:
        return ""

    try:
        reader = PdfReader(file_path)
        partes = []
        for page in reader.pages[:25]:
            texto = page.extract_text() or ""
            if texto:
                partes.append(texto)
            if sum(len(part) for part in partes) >= MAX_EXTRACT_CHARS:
                break
        return "\n".join(partes)[:MAX_EXTRACT_CHARS]
    except Exception:
        return ""


def extract_docx_text(file_path: str) -> str:
    try:
        with zipfile.ZipFile(file_path, "r") as zip_file:
            xml_data = []
            for name in zip_file.namelist():
                if name.startswith("word/") and name.endswith(".xml"):
                    try:
                        xml_data.append(zip_file.read(name).decode("utf-8", errors="ignore"))
                    except Exception:
                        continue
        if not xml_data:
            return ""
        text = " ".join(xml_data)
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:MAX_EXTRACT_CHARS]
    except Exception:
        return ""


def extract_search_text(file_path: str) -> str:
    extension = os.path.splitext(file_path)[1].lower()

    if extension in {
        ".txt", ".md", ".csv", ".json", ".log", ".ini", ".yaml", ".yml",
        ".xml", ".html", ".css", ".js", ".py", ".java", ".ts", ".tsx",
        ".jsx", ".sql", ".sh", ".conf", ".rtf",
    }:
        return extract_plain_text(file_path)

    if extension == ".pdf":
        return extract_pdf_text(file_path)

    if extension in {".docx", ".odt"}:
        return extract_docx_text(file_path)

    return ""


def extract_matching_snippet(file_path: str, query_lower: str) -> str:
    text = extract_search_text(file_path)
    if not text:
        return ""

    text_lower = text.lower()
    index = text_lower.find(query_lower)
    if index == -1:
        return ""

    inicio = max(0, index - 20)
    fin = min(len(text), index + len(query_lower) + 20)
    return text[inicio:fin].strip()


def search_files(query: str, mode: str = "both") -> list[dict]:
    query_lower = query.lower().strip()
    results = []

    search_name = mode in {"both", "name"}
    search_content = mode in {"both", "content"}

    if not query_lower:
        return results

    zones = [("inbox", INBOX_DIR), ("catalog", FILES_DIR)]

    for zone, base_dir in zones:
        if not os.path.exists(base_dir):
            continue

        for root, _, files in os.walk(base_dir):
            for file_name in files:
                if file_name.endswith(".part"):
                    continue

                absolute_path = os.path.join(root, file_name)
                if os.path.islink(absolute_path):
                    continue
                if not is_path_within_base(absolute_path, base_dir):
                    continue
                relative_path = os.path.relpath(absolute_path, base_dir).replace("\\", "/")

                matches_name = search_name and query_lower in file_name.lower()
                matches_content = False
                snippet = ""

                if search_content and is_content_searchable(absolute_path):
                    snippet = extract_matching_snippet(absolute_path, query_lower)
                    matches_content = bool(snippet)

                if not matches_name and not matches_content:
                    continue

                encoded_url = quote(relative_path)
                open_url = f"/drive/open/{zone}/{encoded_url}"
                download_url = f"/drive/download/{zone}/{encoded_url}"

                match_types = []
                if matches_name:
                    match_types.append("nombre")
                if matches_content:
                    match_types.append("contenido")

                results.append({
                    "zone": zone,
                    "name": file_name,
                    "relative_path": relative_path,
                    "size": format_size(os.path.getsize(absolute_path)),
                    "open_url": open_url,
                    "download_url": download_url,
                    "match_type": " + ".join(match_types),
                    "snippet": snippet,
                })

                if len(results) >= MAX_SEARCH_RESULTS:
                    return results

    return results
