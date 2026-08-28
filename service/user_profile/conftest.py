import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


def _encode(image, image_format, **save_kwargs):
    buffer = io.BytesIO()
    image.save(buffer, format=image_format, **save_kwargs)
    return buffer.getvalue()


@pytest.fixture
def make_upload(make_image):
    def _make(image_format="PNG", image=None, filename="picture", **save_kwargs):
        if image is None:
            image = make_image()
        return {
            "picture": SimpleUploadedFile(
                f"{filename}.{image_format.lower()}",
                _encode(image, image_format, **save_kwargs),
                f"image/{image_format.lower()}",
            )
        }

    return _make
