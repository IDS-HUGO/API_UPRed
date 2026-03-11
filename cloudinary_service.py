import cloudinary
import cloudinary.uploader
from config import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


def upload_image(file_bytes: bytes, public_id: str) -> str:
    """Sube imagen a Cloudinary y retorna la URL segura."""
    result = cloudinary.uploader.upload(
        file_bytes,
        public_id=public_id,
        resource_type="image",
        overwrite=True,
    )
    return result["secure_url"]


def delete_image(public_id: str) -> None:
    """Elimina imagen de Cloudinary."""
    cloudinary.uploader.destroy(public_id, resource_type="image")
