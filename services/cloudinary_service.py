import logging

import cloudinary
import cloudinary.uploader
from config import settings

logger = logging.getLogger("upred.cloudinary")


class CloudinaryService:
    def __init__(self) -> None:
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True,
        )

    def is_configured(self) -> bool:
        return bool(
            settings.CLOUDINARY_CLOUD_NAME
            and settings.CLOUDINARY_API_KEY
            and settings.CLOUDINARY_API_SECRET
        )

    def upload_image(self, file_bytes: bytes, public_id: str) -> str:
        if not self.is_configured():
            raise ValueError("Cloudinary no está configurado en variables de entorno")

        try:
            result = cloudinary.uploader.upload(
                file_bytes,
                public_id=public_id,
                resource_type="image",
                overwrite=True,
            )
        except Exception as e:
            logger.exception("Fallo subida Cloudinary public_id=%s", public_id)
            msg = str(e).lower()
            if "401" in msg or "unauthorized" in msg:
                raise ValueError(
                    "Cloudinary rechazo las credenciales (401). Revisa en .env: "
                    "CLOUDINARY_CLOUD_NAME (nombre del cloud en el dashboard, no un placeholder), "
                    "CLOUDINARY_API_KEY y CLOUDINARY_API_SECRET."
                ) from e
            raise ValueError(f"Error al subir imagen a Cloudinary: {e}") from e

        return result["secure_url"]

    def delete_image(self, public_id: str) -> None:
        if not self.is_configured():
            return
        cloudinary.uploader.destroy(public_id, resource_type="image")


cloudinary_service = CloudinaryService()
