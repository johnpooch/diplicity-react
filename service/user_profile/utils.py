import io

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
from PIL import Image, ImageOps, UnidentifiedImageError

from common.constants import GameStatus
from member.models import Member

User = get_user_model()

PICTURE_MAX_BYTES = 5 * 1024 * 1024
PICTURE_MAX_DIMENSION = 8192
PICTURE_SIZE = 256
PICTURE_JPEG_QUALITY = 90
PICTURE_CONTENT_TYPES = {
    "JPEG": "image/jpeg",
    "PNG": "image/png",
    "WEBP": "image/webp",
}


def normalise_picture(upload):
    if upload.size > PICTURE_MAX_BYTES:
        raise ValidationError(f"Picture is too large (max {PICTURE_MAX_BYTES} bytes).")

    try:
        image = Image.open(upload)
    except (UnidentifiedImageError, OSError):
        raise ValidationError("Picture could not be read as an image.")

    if image.format not in PICTURE_CONTENT_TYPES:
        raise ValidationError("Picture must be a JPEG, PNG or WebP image.")

    image_format = image.format
    width, height = image.size
    if width > PICTURE_MAX_DIMENSION or height > PICTURE_MAX_DIMENSION:
        raise ValidationError(
            f"Picture is larger than {PICTURE_MAX_DIMENSION}px on a side."
        )

    image.draft(None, (PICTURE_SIZE, PICTURE_SIZE))

    try:
        oriented = ImageOps.exif_transpose(image)
        cropped = ImageOps.fit(
            oriented, (PICTURE_SIZE, PICTURE_SIZE), method=Image.Resampling.LANCZOS
        )
    except OSError:
        raise ValidationError("Picture could not be decoded.")

    if image_format == "JPEG":
        cropped = cropped.convert("RGB")
    elif cropped.mode not in ("RGB", "RGBA"):
        cropped = cropped.convert("RGBA")

    stripped = Image.frombytes(cropped.mode, cropped.size, cropped.tobytes())

    buffer = io.BytesIO()
    if image_format == "JPEG":
        stripped.save(buffer, format=image_format, quality=PICTURE_JPEG_QUALITY)
    else:
        stripped.save(buffer, format=image_format)
    return buffer.getvalue(), PICTURE_CONTENT_TYPES[image_format]


def get_player_stats(user):
    members = Member.objects.players().filter(user=user, game__sandbox=False)
    total_games = members.filter(
        Q(removed_at__isnull=True, replaced_by__isnull=True)
        | Q(withdrawn_at__isnull=False),
        game__status=GameStatus.COMPLETED,
    ).count()
    active_games = (
        members.holding_seat()
        .filter(game__status=GameStatus.ACTIVE)
        .exclude(pk__in=Member.objects.vacant())
        .count()
    )

    return {
        "total_games": total_games,
        "active_games": active_games,
    }


def user_can_use_bot_opponent(user):
    if user is None or not user.email:
        return False
    return user.email.lower() in settings.BOT_OPPONENT_ALLOWLIST
