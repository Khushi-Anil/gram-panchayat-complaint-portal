import secrets
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError


MAX_IMAGE_BYTES = 5 * 1024 * 1024


def sanitize_image(upload):
    """Validate a small image and re-encode it to remove EXIF and other metadata."""
    if upload.size > MAX_IMAGE_BYTES:
        raise ValidationError("Image must be 5 MB or smaller.")
    extension = upload.name.rsplit(".", 1)[-1].lower() if "." in upload.name else ""
    if extension not in {"jpg", "jpeg", "png", "webp"}:
        raise ValidationError("Choose a JPG, PNG, or WEBP image.")

    try:
        from PIL import Image, ImageOps

        upload.seek(0)
        image = Image.open(upload)
        image.load()
        actual_format = image.format
        if actual_format not in {"JPEG", "PNG", "WEBP"}:
            raise ValidationError("The uploaded file is not a supported image.")
        image = ImageOps.exif_transpose(image)
        if actual_format == "JPEG" and image.mode not in {"RGB", "L"}:
            image = image.convert("RGB")
        image.info.clear()
        output = BytesIO()
        save_options = {"optimize": True}
        if actual_format in {"JPEG", "WEBP"}:
            save_options["quality"] = 88
        image.save(output, format=actual_format, **save_options)
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError("The image is invalid or could not be processed.") from exc

    suffix = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}[actual_format]
    return ContentFile(output.getvalue(), name=f"{secrets.token_hex(16)}.{suffix}")
