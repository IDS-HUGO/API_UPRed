"""
Subida de foto de perfil a Cloudinary con fallback: si falla o no hay config,
no bloquea registro ni edición de perfil (misma idea que publicaciones con fallback).
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from models import Auditoria
from services.cloudinary_service import cloudinary_service

logger = logging.getLogger("upred.profile_photo")


def try_upload_profile_photo(
    *,
    file_bytes: bytes,
    user_id: int,
    db: Session,
    actor_usuario_id: int,
    context: str,
) -> Optional[str]:
    """
    Intenta subir a Cloudinary. Devuelve secure_url o None si no hay config o falla el upload.
    Registra auditoría en fallo (no lanza).
    """
    if not cloudinary_service.is_configured():
        logger.warning(
            "Foto de perfil omitida: Cloudinary no configurado. user_id=%s context=%s",
            user_id,
            context,
        )
        _audit_photo_skip(db, actor_usuario_id, user_id, context, "cloudinary_no_configurado", None)
        return None

    try:
        public_id = f"perfiles/{user_id}"
        return cloudinary_service.upload_image(file_bytes, public_id)
    except Exception as e:
        logger.warning(
            "Foto de perfil no subida a Cloudinary user_id=%s context=%s: %s",
            user_id,
            context,
            e,
            exc_info=True,
        )
        _audit_photo_skip(db, actor_usuario_id, user_id, context, "cloudinary_error", str(e))
        return None


def _audit_photo_skip(
    db: Session,
    actor_usuario_id: int,
    user_id: int,
    context: str,
    reason: str,
    error_detail: Optional[str],
) -> None:
    db.add(
        Auditoria(
            actor_usuario_id=actor_usuario_id,
            accion="foto_perfil_no_guardada",
            entidad="usuarios",
            entidad_id=str(user_id),
            detalle={
                "context": context,
                "reason": reason,
                "error": error_detail,
            },
        )
    )
