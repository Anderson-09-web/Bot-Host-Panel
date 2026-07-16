"""
Servicio Cloudflare R2 usando boto3.
Gestión completa de archivos: subir, descargar, eliminar, listar, backups.
"""
import os
import logging
from typing import BinaryIO
import boto3
from botocore.client import Config as BotoConfig
from botocore.exceptions import ClientError
from config.settings import Config

logger = logging.getLogger("r2_service")

_client = None


def get_client():
    """Retorna el cliente R2 (singleton)."""
    global _client
    if _client is None:
        if not all([Config.R2_ENDPOINT, Config.R2_ACCESS_KEY, Config.R2_SECRET_KEY]):
            raise RuntimeError("Credenciales R2 no configuradas.")
        _client = boto3.client(
            "s3",
            endpoint_url=Config.R2_ENDPOINT,
            aws_access_key_id=Config.R2_ACCESS_KEY,
            aws_secret_access_key=Config.R2_SECRET_KEY,
            config=BotoConfig(signature_version="s3v4"),
            region_name="auto",
        )
    return _client


def upload_file(local_path: str, key: str, content_type: str = "application/octet-stream") -> dict:
    """Sube un archivo local a R2."""
    try:
        client = get_client()
        client.upload_file(
            local_path,
            Config.R2_BUCKET,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        url = f"{Config.R2_PUBLIC_URL}/{key}" if Config.R2_PUBLIC_URL else None
        logger.info(f"[R2] Archivo subido: {key}")
        return {"success": True, "key": key, "url": url}
    except Exception as e:
        logger.error(f"[R2] Error subiendo {key}: {e}")
        return {"success": False, "error": str(e)}


def upload_fileobj(file_obj: BinaryIO, key: str, content_type: str = "application/octet-stream") -> dict:
    """Sube un objeto de archivo (stream) a R2."""
    try:
        client = get_client()
        client.upload_fileobj(
            file_obj,
            Config.R2_BUCKET,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        url = f"{Config.R2_PUBLIC_URL}/{key}" if Config.R2_PUBLIC_URL else None
        logger.info(f"[R2] FileObj subido: {key}")
        return {"success": True, "key": key, "url": url}
    except Exception as e:
        logger.error(f"[R2] Error subiendo fileobj {key}: {e}")
        return {"success": False, "error": str(e)}


def download_file(key: str, local_path: str) -> dict:
    """Descarga un archivo de R2 a una ruta local."""
    try:
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        get_client().download_file(Config.R2_BUCKET, key, local_path)
        logger.info(f"[R2] Descargado: {key} → {local_path}")
        return {"success": True, "local_path": local_path}
    except Exception as e:
        logger.error(f"[R2] Error descargando {key}: {e}")
        return {"success": False, "error": str(e)}


def delete_file(key: str) -> dict:
    """Elimina un archivo de R2."""
    try:
        get_client().delete_object(Bucket=Config.R2_BUCKET, Key=key)
        logger.info(f"[R2] Eliminado: {key}")
        return {"success": True}
    except Exception as e:
        logger.error(f"[R2] Error eliminando {key}: {e}")
        return {"success": False, "error": str(e)}


def list_files(prefix: str = "") -> dict:
    """Lista archivos en el bucket con un prefijo opcional."""
    try:
        response = get_client().list_objects_v2(Bucket=Config.R2_BUCKET, Prefix=prefix)
        files = []
        for obj in response.get("Contents", []):
            key = obj["Key"]
            files.append(
                {
                    "key": key,
                    "size": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                    "url": f"{Config.R2_PUBLIC_URL}/{key}" if Config.R2_PUBLIC_URL else None,
                }
            )
        return {"success": True, "files": files, "count": len(files)}
    except Exception as e:
        logger.error(f"[R2] Error listando archivos: {e}")
        return {"success": False, "error": str(e), "files": []}


def get_public_url(key: str) -> str | None:
    """Retorna la URL pública de un objeto."""
    if Config.R2_PUBLIC_URL:
        return f"{Config.R2_PUBLIC_URL}/{key}"
    return None


def is_configured() -> bool:
    """Verifica si R2 está configurado."""
    return bool(Config.R2_ENDPOINT and Config.R2_ACCESS_KEY and Config.R2_SECRET_KEY and Config.R2_BUCKET)
