import cloudinary
import cloudinary.uploader
from config import settings


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

        result = cloudinary.uploader.upload(
            file_bytes,
            public_id=public_id,
            resource_type="image",
            overwrite=True,
        )
        return result["secure_url"]

    def delete_image(self, public_id: str) -> None:
        if not self.is_configured():
            return
        cloudinary.uploader.destroy(public_id, resource_type="image")


cloudinary_service = CloudinaryService()
