"""Utilidades generales."""
import os
import zipfile
import shutil
import humanize
from datetime import datetime, timezone
from pathlib import Path


def format_bytes(size: int) -> str:
    """Convierte bytes a formato legible."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def safe_path(base: str, rel: str) -> str | None:
    """
    Valida que `rel` no salga del directorio `base`.
    Retorna la ruta absoluta o None si es inválida.
    """
    base = os.path.realpath(base)
    target = os.path.realpath(os.path.join(base, rel.lstrip("/")))
    if target.startswith(base):
        return target
    return None


def list_directory(path: str) -> list[dict]:
    """Lista el contenido de un directorio."""
    items = []
    try:
        for entry in sorted(os.scandir(path), key=lambda e: (not e.is_dir(), e.name.lower())):
            stat = entry.stat()
            items.append(
                {
                    "name": entry.name,
                    "is_dir": entry.is_dir(),
                    "size": format_bytes(stat.st_size) if not entry.is_dir() else "—",
                    "size_bytes": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                    "extension": Path(entry.name).suffix.lower() if not entry.is_dir() else "",
                }
            )
    except PermissionError:
        pass
    return items


def extract_zip(zip_path: str, dest_dir: str) -> bool:
    """Extrae un ZIP en el directorio destino."""
    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            z.extractall(dest_dir)
        return True
    except Exception:
        return False


def compress_folder(folder_path: str, output_zip: str) -> bool:
    """Comprime una carpeta en ZIP."""
    try:
        shutil.make_archive(output_zip.replace(".zip", ""), "zip", folder_path)
        return True
    except Exception:
        return False


def get_file_icon(filename: str) -> str:
    """Retorna un icono Font Awesome para el tipo de archivo."""
    ext = Path(filename).suffix.lower()
    icons = {
        ".py": "fa-brands fa-python",
        ".js": "fa-brands fa-js",
        ".html": "fa-brands fa-html5",
        ".css": "fa-brands fa-css3-alt",
        ".json": "fa-solid fa-brackets-curly",
        ".md": "fa-brands fa-markdown",
        ".txt": "fa-solid fa-file-lines",
        ".zip": "fa-solid fa-file-zipper",
        ".png": "fa-solid fa-file-image",
        ".jpg": "fa-solid fa-file-image",
        ".jpeg": "fa-solid fa-file-image",
        ".gif": "fa-solid fa-file-image",
        ".mp3": "fa-solid fa-file-audio",
        ".mp4": "fa-solid fa-file-video",
        ".pdf": "fa-solid fa-file-pdf",
        ".env": "fa-solid fa-shield-halved",
        ".toml": "fa-solid fa-gear",
        ".yml": "fa-solid fa-gear",
        ".yaml": "fa-solid fa-gear",
        ".sh": "fa-solid fa-terminal",
        ".log": "fa-solid fa-scroll",
        ".db": "fa-solid fa-database",
    }
    return icons.get(ext, "fa-solid fa-file")
