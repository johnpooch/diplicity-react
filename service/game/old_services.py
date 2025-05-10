import json
import os
import random
import requests
from datetime import datetime, timedelta
from django.utils import timezone

from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction, models
from django.shortcuts import get_object_or_404
from fcm_django.models import FCMDevice
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from rest_framework import exceptions
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Game,
    Variant,
    Order,
    Phase,
    Channel,
    ChannelMessage,
    UserProfile,
    Task,
    Unit,
    SupplyCenter,
)
from . import serializers
from .tasks import BaseTask


def adjudication_start(game_id: int):
    game = Game.objects.filter(id=game_id).first()
    if not game:
        raise exceptions.ValidationError(
            detail=f"Game with id {game_id} does not exist."
        )

    response = requests.get(
        f"https://godip-adjudication.appspot.com/start-with-options/{game.variant.name}",
    )
    response.raise_for_status()
    data = response.json()
    if isinstance(data, str):
        data = json.loads(data)
    serializer = serializers.AdjudicationResponseSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def auth_generate_username(name):
    username = "".join(name.split(" ")).lower()
    User = get_user_model()
    if not User.objects.filter(username=username).exists():
        return username
    else:
        random_username = username + str(random.randint(0, 1000))
        return auth_generate_username(random_username)


def auth_get_tokens(user):
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


def auth_login_or_register(id_token):
    try:
        id_info = google_id_token.verify_oauth2_token(
            id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=3,
        )
    except GoogleAuthError as e:
        raise exceptions.AuthenticationFailed(f"Token verification failed: {str(e)}")
    except ValueError:
        raise exceptions.AuthenticationFailed("Token verification failed")

    if id_info["iss"] not in [
        "accounts.google.com",
        "https://accounts.google.com",
    ]:
        raise exceptions.AuthenticationFailed("Wrong issuer")

    email = id_info.get("email")
    name = id_info.get("name")
    picture = id_info.get("picture")

    User = get_user_model()
    existing_user = User.objects.filter(email=email).first()
    if existing_user:
        # Update UserProfile for existing user
        profile = UserProfile.objects.filter(user=existing_user).first()
        if not profile:
            UserProfile.objects.create(user=existing_user, name=name, picture=picture)
        else:
            profile.name = name
            profile.picture = picture
            profile.save()
        return existing_user
    else:
        user = {
            "email": email,
            "username": auth_generate_username(name),
            "password": os.environ.get("SOCIAL_SECRET"),
        }
        user = User.objects.create_user(**user)
        user.is_verified = True
        user.save()

        # Create UserProfile for new user
        UserProfile.objects.create(user=user, name=name, picture=picture)
        return user


def game_create(user, data: dict):
    variant = Variant.objects.filter(id=data["variant"]).first()
    if not variant:
        raise exceptions.ValidationError(
            detail=f"Variant with name {data['variant']} does not exist."
        )

    with transaction.atomic():
        game = Game.objects.create(name=data["name"], variant=variant)
        game.members.create(user=user)

        # Create the initial phase
        phase = game.phases.create(
            game=game,
            season=variant.start["season"],
            year=variant.start["year"],
            phase_type=variant.start["phase_type"],
        )

        # Create Unit instances for the phase
        for unit_data in variant.start["units"]:
            Unit.objects.create(
                phase=phase,
                unit_type=unit_data["unit_type"].lower(),
                nation=unit_data["nation"],
                province=unit_data["province"],
            )

        # Create SupplyCenter instances for the phase
        for sc_data in variant.start["supply_centers"]:
            SupplyCenter.objects.create(
                phase=phase,
                nation=sc_data["nation"],
                province=sc_data["province"],
            )

    return game


def game_join(user, game_id: int):
    game = get_object_or_404(Game, id=game_id)

    if game.status != Game.PENDING:
        raise exceptions.PermissionDenied(detail="Cannot join a non-pending game.")

    if game.members.filter(user=user).exists():
        raise exceptions.ValidationError(detail="User is already a member of the game.")

    game.members.create(user=user)

    if len(game.variant.nations) == game.members.count():
        game_start(game.id)

    return game


def game_leave(user, game_id: int):
    game = get_object_or_404(Game, id=game_id)

    if game.status != Game.PENDING:
        raise exceptions.PermissionDenied(detail="Cannot leave a non-pending game.")

    member = game.members.filter(user=user).first()
    if not member:
        raise exceptions.ValidationError(detail="User is not a member of the game.")

    member.delete()

    return game


def game_list(user, filters=None):
    filters = filters or {}
    if filters.get("mine") is True:
        return Game.objects.filter(members__user=user).distinct()
    if filters.get("can_join") is True:
        return (
            Game.objects.filter(status=Game.PENDING)
            .exclude(members__user=user)
            .distinct()
        )
    return Game.objects.all().distinct()


@shared_task(base=BaseTask)
def game_start(game_id: int):
    game = Game.objects.filter(id=game_id).first()
    if not game:
        raise exceptions.ValidationError(
            detail=f"Game with id {game_id} does not exist."
        )

    if game.status != Game.PENDING:
        raise exceptions.PermissionDenied(detail="Cannot start a non-pending game.")

    nations = game.variant.nations
    random.shuffle(nations)

    try:
        adjudication_response = adjudication_start(game_id)
    except Exception as e:
        raise exceptions.ValidationError(
            detail=f"Failed to start game with adjudication service: {str(e)}"
        )

    options_data = adjudication_response["options"]

    with transaction.atomic():
        current_phase = game.current_phase

        for member in game.members.all():
            nation = nations.pop()
            member.nation = nation["name"]
            member.phase_states.create(
                phase=current_phase, options=options_data[member.nation]
            )
            member.save()

        current_phase.status = Phase.ACTIVE
        current_phase.save()

        game.status = Game.ACTIVE
        game.save()

        # Create resolution task when game starts
        _create_resolution_task(game, game.get_phase_duration_seconds())

        # Create public press channel
        public_channel = game.channels.create(
            name="Public Press",
            private=False,
        )
        public_channel.members.set(game.members.all())

    user_ids = [member.user.id for member in game.members.all()]
    notification_data = {
        "title": "Game started",
        "body": f"The game '{game.name}' has started!",
        "type": "game_start",
        "game_id": game.id,
    }

    notification_create(user_ids, notification_data)


def order_create(user, game_id: int, data: dict):
    game = get_object_or_404(Game, id=game_id)

    member = game.members.filter(user=user).first()
    if not member:
        raise exceptions.PermissionDenied(detail="User is not a member of the game.")

    if member.eliminated:
        raise exceptions.PermissionDenied(
            detail="Cannot create orders for eliminated players."
        )

    if member.kicked:
        raise exceptions.PermissionDenied(
            detail="Cannot create orders for kicked players."
        )

    if game.status != Game.ACTIVE:
        raise exceptions.ValidationError(
            detail="Orders can only be created for active games."
        )

    current_phase = game.current_phase
    if current_phase is None:
        raise exceptions.ValidationError(detail="No current phase found for the game.")

    current_phase_state = current_phase.phase_states.filter(member__user=user).first()
    if current_phase_state.eliminated:
        raise exceptions.PermissionDenied(
            detail="Cannot create orders for eliminated players."
        )

    order = Order.objects.create(
        phase_state=current_phase_state,
        order_type=data["order_type"],
        source=data["source"],
        target=data.get("target"),
        aux=data.get("aux"),
    )

    try:
        order.full_clean()
    except Exception as e:
        raise exceptions.ValidationError(detail=str(e))

    order.save()

    return order


@shared_task(base=BaseTask)
def notification_create(user_ids: list, data: dict):
    message = {
        "notification": {
            "title": data["title"],
            "body": data["body"],
        },
        "data": {
            "type": data.get("type", ""),
            "game_id": str(data.get("game_id", "")),
            "channel_id": str(data.get("channel_id", "")),
        },
    }
    devices = FCMDevice.objects.filter(user__id__in=user_ids)
    devices.send_message(message)


def phase_state_confirm(user, game_id: int):
    game = get_object_or_404(Game, id=game_id)

    if game.status != Game.ACTIVE:
        raise exceptions.ValidationError(detail="Game is not active.")

    member = game.members.filter(user=user).first()
    if not member:
        raise exceptions.ValidationError(detail="User is not a member of the game.")

    if member.eliminated:
        raise exceptions.ValidationError(detail="User is eliminated from the game.")

    if member.kicked:
        raise exceptions.ValidationError(detail="User is kicked from the game.")

    current_phase = game.phases.last()
    if not current_phase:
        raise exceptions.ValidationError(detail="No current phase found for the game.")

    phase_state = current_phase.phase_states.filter(member=member).first()
    if not phase_state:
        raise exceptions.ValidationError(detail="No phase state found for the user.")

    phase_state.orders_confirmed = not phase_state.orders_confirmed
    phase_state.save()
    return phase_state


def game_retrieve(user, game_id: int):
    return get_object_or_404(Game, id=game_id)


def variant_list():
    variants = Variant.objects.all()
    return variants


def channel_create(user, game_id: int, member_ids: list):
    game = get_object_or_404(Game, id=game_id)

    if game.status != Game.ACTIVE:
        raise exceptions.ValidationError("Game is not active.")

    member = game.members.filter(user=user).first()

    if not member:
        raise exceptions.PermissionDenied("User is not a member of the game.")

    if not member_ids:
        raise exceptions.ValidationError("Members list cannot be empty.")

    member_ids = member_ids + [member.id]

    channel_members = game.members.filter(id__in=member_ids)
    if channel_members.count() != len(member_ids):
        raise exceptions.ValidationError(
            "One or more members are not part of the game."
        )

    nations = sorted([m.nation for m in channel_members])
    channel_name = ", ".join(nations)

    if game.channels.filter(name=channel_name).exists():
        raise exceptions.ValidationError(
            "A channel with the same members already exists."
        )

    channel = Channel.objects.create(
        name=channel_name,
        private=True,
        game=game,
    )
    channel.members.set(channel_members)
    return channel


def channel_message_create(user, game_id: int, channel_id: int, data: dict):
    game = get_object_or_404(Game, id=game_id)

    if game.status != Game.ACTIVE:
        raise exceptions.ValidationError("Game is not active.")

    channel = get_object_or_404(Channel, id=channel_id, game=game)

    member = game.members.filter(user=user).first()
    if not member:
        raise exceptions.PermissionDenied("User is not a member of the game.")

    if not channel.members.filter(id=member.id).exists():
        raise exceptions.PermissionDenied("User is not a member of the channel.")

    body = data.get("body", "").strip()
    if not body:
        raise exceptions.ValidationError("Message content cannot be empty.")

    if len(body) > 1000:  # Example reasonable limit
        raise exceptions.ValidationError("Message content exceeds the maximum length.")

    message = ChannelMessage.objects.create(
        channel=channel,
        sender=member,
        body=body,
    )

    # Notify other members in the channel
    other_members = channel.members.exclude(id=member.id)
    user_ids = [m.user.id for m in other_members]
    notification_data = {
        "title": "New Message",
        "body": f"{member.user.username} sent a message in {channel.name}.",
        "type": "channel_message",
        "game_id": str(game_id),
        "channel_id": str(channel_id),
    }
    notification_create(user_ids, notification_data)

    return message


def channel_list(user):
    user_member_ids = user.members.values_list("id", flat=True)
    return Channel.objects.filter(
        models.Q(private=False) | models.Q(members__id__in=user_member_ids)
    ).distinct()


def adjudication_resolve(game_id: int):
    game = Game.objects.filter(id=game_id).first()
    if not game:
        raise exceptions.ValidationError(
            detail=f"Game with id {game_id} does not exist."
        )

    # Format orders
    formatted_orders = {}
    current_phase = game.current_phase
    phase_states = current_phase.phase_states.all()

    for phase_state in phase_states:
        nation = phase_state.member.nation
        if nation not in formatted_orders:
            formatted_orders[nation] = {}

        for order in phase_state.orders.all():
            formatted_orders[nation][order.source] = [order.order_type, order.target]

            # Only include aux if it exists (Support/Convoy orders)
            if order.aux:
                formatted_orders[nation][order.source].append(order.aux)

    serialized_game = serializers.PhaseSerializer(
        data={
            "Season": game.current_phase.season,
            "Year": game.current_phase.year,
            "Type": game.current_phase.phase_type,
            "Units": list(game.current_phase.units.all()),
            "Orders": formatted_orders,
            "SupplyCenters": list(game.current_phase.supply_centers.all()),
            "Dislodgeds": {},
            "Dislodgers": {},
            "Bounces": {},
            "Resolutions": {},
        }
    )

    serialized_game.is_valid(raise_exception=True)

    response = requests.post(
        f"https://godip-adjudication.appspot.com/resolve-with-options/{game.variant.name}",
        json=serialized_game.data,
        headers={
            "Content-Type": "application/json",
        },
    )
    response.raise_for_status()
    data = response.json()
    if isinstance(data, str):
        data = json.loads(data)
    serializer = serializers.AdjudicationResponseSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    return serializer.validated_data


def _create_resolution_task(game, delay_seconds):
    scheduled_for = timezone.now() + timedelta(seconds=delay_seconds)
    task_result = game_resolve.apply_async(
        args=[game.id], kwargs={}, countdown=delay_seconds
    )

    # Get the task object created by BaseTask
    task = Task.objects.get(id=task_result.task_id)
    task.scheduled_for = scheduled_for
    task.save()

    game.resolution_task = task
    game.save()
    return task


@shared_task(base=BaseTask)
def game_resolve(game_id: int):
    game = Game.objects.filter(id=game_id).first()
    if not game:
        raise exceptions.ValidationError(
            detail=f"Game with id {game_id} does not exist."
        )

    if game.resolution_task:
        game.resolution_task.status = Task.COMPLETED
        game.resolution_task.save()
        game.resolution_task = None
        game.save()

    if game.status != Game.ACTIVE:
        raise exceptions.ValidationError("Cannot resolve a non-active game.")

    try:
        adjudication_response = adjudication_resolve(game_id)
    except Exception as e:
        raise exceptions.ValidationError(
            detail=f"Failed to resolve game with adjudication service: {str(e)}"
        )

    phase_data = adjudication_response["phase"]
    options_data = adjudication_response["options"]

    with transaction.atomic():
        # Create new phase
        new_phase = game.phases.create(
            season=phase_data["season"],
            year=phase_data["year"],
            phase_type=phase_data["phase_type"],
            units=phase_data["units"],
            orders=phase_data["orders"],
            supply_centers=phase_data["supply_centers"],
            dislodgeds=phase_data["dislodgeds"],
            dislodgers=phase_data["dislodgers"],
            bounces=phase_data["bounces"],
            resolutions=phase_data["resolutions"],
            status=Phase.ACTIVE,
        )

        # Create phase states for all members
        for member in game.members.all():
            new_phase.phase_states.create(
                member=member, options=options_data[member.nation]
            )

        # Schedule next resolution if game is still active
        if game.status == Game.ACTIVE:
            _create_resolution_task(game, game.get_phase_duration_seconds())

    # Notify members
    user_ids = [member.user.id for member in game.members.all()]
    notification_data = {
        "title": "Phase Resolved",
        "body": f"Phase {game.current_phase.name} has been resolved. New phase: {new_phase.name}",
        "type": "game_resolve",
        "game_id": game.id,
    }

    notification_create(user_ids, notification_data)

    return new_phase
