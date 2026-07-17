"""Rutas del explorador de archivos."""
import os
import shutil
import logging
from pathlib import Path
from flask import (
    Blueprint, render_template, jsonify, request,
    send_file, abort, current_app
)
from flask_login import login_required
from werkzeug.utils import secure_filename
from utils.helpers import safe_path, list_directory, extract_zip, compress_folder, get_file_icon

files_bp = Blueprint("files", __name__)
logger = logging.getLogger("files")

# Directorio raíz de archivos del bot
BOT_FILES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot_files")


def get_base():
    os.makedirs(BOT_FILES_DIR, exist_ok=True)
    return BOT_FILES_DIR


@files_bp.route("/files")
@login_required
def index():
    return render_template("files.html")


@files_bp.route("/api/files/list")
@login_required
def api_list():
    rel = request.args.get("path", "")
    base = get_base()
    target = safe_path(base, rel)
    if not target or not os.path.isdir(target):
        return jsonify({"error": "Ruta inválida"}), 400
    items = list_directory(target)
    for item in items:
        item["icon"] = get_file_icon(item["name"]) if not item["is_dir"] else "fa-solid fa-folder"
    rel_path = os.path.relpath(target, base)
    breadcrumbs = _build_breadcrumbs(rel_path)
    return jsonify({"items": items, "current": rel_path, "breadcrumbs": breadcrumbs})


@files_bp.route("/api/files/read")
@login_required
def api_read():
    rel = request.args.get("path", "")
    base = get_base()
    target = safe_path(base, rel)
    if not target or not os.path.isfile(target):
        return jsonify({"error": "Archivo no encontrado"}), 404
    try:
        with open(target, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(500_000)  # max 500KB en texto
        return jsonify({"success": True, "content": content, "path": rel})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@files_bp.route("/api/files/write", methods=["POST"])
@login_required
def api_write():
    data = request.get_json(silent=True) or {}
    rel = data.get("path", "")
    content = data.get("content", "")
    restart = data.get("restart_bot", True)
    base = get_base()
    target = safe_path(base, rel)
    if not target:
        return jsonify({"error": "Ruta inválida"}), 400
    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        # Sync a R2
        _sync_to_r2(target, rel)
        # Reiniciar bot si es archivo Python del bot
        if restart and rel.endswith(".py"):
            _restart_bot_async()
        return jsonify({"success": True, "restarted": restart and rel.endswith(".py")})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@files_bp.route("/api/files/create_folder", methods=["POST"])
@login_required
def api_create_folder():
    data = request.get_json(silent=True) or {}
    rel = data.get("path", "")
    base = get_base()
    target = safe_path(base, rel)
    if not target:
        return jsonify({"error": "Ruta inválida"}), 400
    try:
        os.makedirs(target, exist_ok=True)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@files_bp.route("/api/files/delete", methods=["POST"])
@login_required
def api_delete():
    data = request.get_json(silent=True) or {}
    rel = data.get("path", "")
    base = get_base()
    target = safe_path(base, rel)
    if not target or target == base:
        return jsonify({"error": "Ruta inválida"}), 400
    try:
        is_dir = os.path.isdir(target)
        if is_dir:
            # Borrar cada archivo de R2 antes de eliminar localmente
            for root, dirs, files in os.walk(target):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    frel = os.path.relpath(fpath, base)
                    _delete_from_r2(frel)
            shutil.rmtree(target)
        else:
            _delete_from_r2(rel)
            os.remove(target)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@files_bp.route("/api/files/rename", methods=["POST"])
@login_required
def api_rename():
    data = request.get_json(silent=True) or {}
    old_rel = data.get("old_path", "")
    new_rel = data.get("new_path", "")
    base = get_base()
    old = safe_path(base, old_rel)
    new = safe_path(base, new_rel)
    if not old or not new:
        return jsonify({"error": "Ruta inválida"}), 400
    try:
        os.rename(old, new)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@files_bp.route("/api/files/copy", methods=["POST"])
@login_required
def api_copy():
    data = request.get_json(silent=True) or {}
    src_rel = data.get("src", "")
    dst_rel = data.get("dst", "")
    base = get_base()
    src = safe_path(base, src_rel)
    dst = safe_path(base, dst_rel)
    if not src or not dst:
        return jsonify({"error": "Ruta inválida"}), 400
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@files_bp.route("/api/files/move", methods=["POST"])
@login_required
def api_move():
    data = request.get_json(silent=True) or {}
    src_rel = data.get("src", "")
    dst_rel = data.get("dst", "")
    base = get_base()
    src = safe_path(base, src_rel)
    dst = safe_path(base, dst_rel)
    if not src or not dst:
        return jsonify({"error": "Ruta inválida"}), 400
    try:
        shutil.move(src, dst)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@files_bp.route("/api/files/download")
@login_required
def api_download():
    rel = request.args.get("path", "")
    base = get_base()
    target = safe_path(base, rel)
    if not target or not os.path.isfile(target):
        abort(404)
    return send_file(target, as_attachment=True)


@files_bp.route("/api/files/upload", methods=["POST"])
@login_required
def api_upload():
    rel_dir = request.form.get("path", "")
    base = get_base()
    target_dir = safe_path(base, rel_dir)
    if not target_dir:
        return jsonify({"error": "Ruta inválida"}), 400
    os.makedirs(target_dir, exist_ok=True)

    uploaded = []
    for file in request.files.getlist("files"):
        filename = secure_filename(file.filename)
        if not filename:
            continue
        dest = os.path.join(target_dir, filename)
        file.save(dest)
        # Auto-extraer ZIP
        if filename.lower().endswith(".zip"):
            extract_zip(dest, target_dir)
            os.remove(dest)
            uploaded.append(f"{filename} (extraído)")
            # Sync todos los archivos extraídos a R2
            for root, dirs, files_list in os.walk(target_dir):
                for fname in files_list:
                    fpath = os.path.join(root, fname)
                    frel = os.path.relpath(fpath, get_base())
                    _sync_to_r2(fpath, frel)
        else:
            rel_dest = os.path.relpath(dest, get_base())
            _sync_to_r2(dest, rel_dest)
            uploaded.append(filename)

    return jsonify({"success": True, "uploaded": uploaded})


@files_bp.route("/api/files/compress", methods=["POST"])
@login_required
def api_compress():
    data = request.get_json(silent=True) or {}
    rel = data.get("path", "")
    base = get_base()
    target = safe_path(base, rel)
    if not target or not os.path.isdir(target):
        return jsonify({"error": "Ruta inválida"}), 400
    out_zip = target + ".zip"
    success = compress_folder(target, out_zip)
    return jsonify({"success": success, "zip": os.path.relpath(out_zip, base)})


@files_bp.route("/api/files/search")
@login_required
def api_search():
    query = request.args.get("q", "").lower()
    base = get_base()
    results = []
    for root, dirs, files in os.walk(base):
        for fname in files:
            if query in fname.lower():
                full = os.path.join(root, fname)
                rel = os.path.relpath(full, base)
                results.append({
                    "name": fname,
                    "path": rel,
                    "is_dir": False,
                    "icon": get_file_icon(fname),
                })
            if len(results) >= 50:
                break
        if len(results) >= 50:
            break
    return jsonify({"results": results})


def _sync_to_r2(local_path: str, r2_key: str):
    """Sube un archivo local a R2 en segundo plano (silencioso si no configurado)."""
    try:
        from services import r2_service
        if not r2_service.is_configured():
            return
        import threading
        # Normalizar key: quitar backslashes de Windows
        key = r2_key.replace("\\", "/")
        threading.Thread(
            target=r2_service.upload_file,
            args=(local_path, key),
            daemon=True,
        ).start()
    except Exception:
        pass


def _delete_from_r2(r2_key: str):
    """Elimina un objeto de R2 (silencioso si no configurado)."""
    try:
        from services import r2_service
        if not r2_service.is_configured():
            return
        key = r2_key.replace("\\", "/")
        r2_service.delete_file(key)
    except Exception:
        pass


def _restart_bot_async():
    """Reinicia el bot en un hilo aparte para no bloquear la respuesta."""
    import threading
    def _do():
        import time
        time.sleep(0.5)
        try:
            from services import bot_manager
            if bot_manager.get_status()["running"]:
                bot_manager.restart_bot()
        except Exception:
            pass
    threading.Thread(target=_do, daemon=True).start()


def _build_breadcrumbs(rel_path: str) -> list[dict]:
    if rel_path in ("", "."):
        return [{"name": "Inicio", "path": ""}]
    parts = rel_path.replace("\\", "/").split("/")
    crumbs = [{"name": "Inicio", "path": ""}]
    accumulated = ""
    for part in parts:
        accumulated = f"{accumulated}/{part}".lstrip("/")
        crumbs.append({"name": part, "path": accumulated})
    return crumbs
