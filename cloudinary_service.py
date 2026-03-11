from services.cloudinary_service import cloudinary_service


def upload_image(file_bytes: bytes, public_id: str) -> str:
    return cloudinary_service.upload_image(file_bytes, public_id)


def delete_image(public_id: str) -> None:
    cloudinary_service.delete_image(public_id)
