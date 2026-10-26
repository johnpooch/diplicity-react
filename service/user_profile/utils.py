import io

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.models import Q
from PIL import Image, ImageOps, UnidentifiedImageError

from common.constants import GameStatus
from member.models import Member
from phase.models import PhaseState
from victory.models import Victory

User = get_user_model()

RECENT_GAME_WINDOW = 10

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
    completed_members = (
        Member.objects.filter(
            Q(removed_at__isnull=True, replaced_by__isnull=True)
            | Q(withdrawn_at__isnull=False),
            user=user,
            game__status=GameStatus.COMPLETED,
            game__sandbox=False,
        )
        .select_related("game")
        .order_by("-game__finished_at")
    )

    total_games = completed_members.count()
    solo_wins = (
        Victory.objects.solo_victories()
        .filter(members__in=completed_members.filter(drew=False))
        .count()
    )
    draws = completed_members.filter(drew=True).count()
    losses = total_games - solo_wins - draws

    last_n_members = list(completed_members[:RECENT_GAME_WINDOW])
    last_n_member_ids = [m.id for m in last_n_members]

    phase_states_with_orders = PhaseState.objects.filter(
        member_id__in=last_n_member_ids,
        has_possible_orders=True,
        phase__status="completed",
    ).exclude(member__withdrawn_at__isnull=False, orders_outcome__isnull=True)
    total_phases = phase_states_with_orders.count()
    nmr_phases = phase_states_with_orders.filter(
        orders_outcome=PhaseState.OrdersOutcome.NMR
    ).count()
    nmr_rate = nmr_phases / total_phases if total_phases > 0 else 0.0

    cd_count = sum(1 for m in last_n_members if m.civil_disorder)
    cd_rate = cd_count / len(last_n_members) if last_n_members else 0.0

    return {
        "total_games": total_games,
        "solo_wins": solo_wins,
        "draws": draws,
        "losses": losses,
        "nmr_rate": round(nmr_rate, 4),
        "cd_rate": round(cd_rate, 4),
    }


def user_can_use_bot_opponent(user):
    if user is None or not user.email:
        return False
    return user.email.lower() in settings.BOT_OPPONENT_ALLOWLIST
