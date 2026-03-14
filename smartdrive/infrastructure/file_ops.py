import os
import shutil


def path_exists(path: str) -> bool:
    return os.path.exists(path)


def is_file(path: str) -> bool:
    return os.path.isfile(path)


def is_dir(path: str) -> bool:
    return os.path.isdir(path)


def delete_file(path: str) -> None:
    os.remove(path)


def create_directory(path: str) -> None:
    os.makedirs(path)


def ensure_directory(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def rename_path(source_path: str, target_path: str) -> None:
    os.rename(source_path, target_path)


def delete_empty_directory(path: str) -> None:
    os.rmdir(path)


def build_zip_archive(source_path: str, temp_dir: str = "/tmp") -> tuple[str, str]:
    folder_name = os.path.basename(source_path)
    zip_filename = f"{folder_name}.zip"
    zip_path = os.path.join(temp_dir, zip_filename)
    shutil.make_archive(zip_path.replace(".zip", ""), "zip", source_path)
    return zip_path, zip_filename


def move_file_sync(source_path: str, target_path: str) -> None:
    shutil.move(source_path, target_path)


def safe_remove_file(path: str) -> None:
    try:
        os.remove(path)
    except Exception:
        pass
