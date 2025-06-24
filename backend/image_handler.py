from PIL import Image, ExifTags
import io
import base64

def compress_image(image_bytes, quality=60):
    image = Image.open(io.BytesIO(image_bytes))
    buffer = io.BytesIO()
    image.save(buffer, format=image.format, optimize=True, quality=quality)
    return buffer.getvalue()

def resize_image(image_bytes, width, height):
    image = Image.open(io.BytesIO(image_bytes))
    resized = image.resize((width, height))
    buffer = io.BytesIO()
    resized.save(buffer, format=image.format)
    return buffer.getvalue()

def extract_metadata(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    metadata = {}
    if hasattr(image, '_getexif'):
        exif_data = image._getexif()
        if exif_data:
            for tag, value in exif_data.items():
                decoded = ExifTags.TAGS.get(tag, tag)
                metadata[decoded] = str(value)
    return metadata

def image_bytes_to_base64(image_bytes):
    return base64.b64encode(image_bytes).decode("utf-8")
