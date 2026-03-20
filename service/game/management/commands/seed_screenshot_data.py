import json
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from channel.models import Channel, ChannelMember, ChannelMessage
from common.constants import (
    DeadlineMode,
    GameStatus,
    MovementPhaseDuration,
    OrderResolutionStatus,
    OrderType,
    PhaseStatus,
    UnitType,
)
from game.models import Game
from login.models import AuthUser
from member.models import Member
from order.models import Order, OrderResolution
from phase.models import Phase
from supply_center.models import SupplyCenter
from unit.models import Unit
from user_profile.models import UserProfile
from variant.models import Variant

SCREENSHOT_EMAIL_PREFIX = "screenshot-"
SCREENSHOT_EMAIL_SUFFIX = "@test.com"
SCREENSHOT_GAME_PREFIX = "screenshot:"

USERS = [
    {"key": "england", "name": "Catherine de Medici", "nation": "England"},
    {"key": "france", "name": "François Lemaire", "nation": "France"},
    {"key": "germany", "name": "Gustav von Stahl", "nation": "Germany"},
    {"key": "italy", "name": "Isabella Rossi", "nation": "Italy"},
    {"key": "austria", "name": "Anton Habsburg", "nation": "Austria"},
    {"key": "turkey", "name": "Tariq Pasha", "nation": "Turkey"},
    {"key": "russia", "name": "Natasha Volkov", "nation": "Russia"},
]

STARTING_UNITS = {
    "ank": ("Fleet", "Turkey"),
    "ber": ("Army", "Germany"),
    "bre": ("Fleet", "France"),
    "bud": ("Army", "Austria"),
    "con": ("Army", "Turkey"),
    "edi": ("Fleet", "England"),
    "kie": ("Fleet", "Germany"),
    "lon": ("Fleet", "England"),
    "lvp": ("Army", "England"),
    "mar": ("Army", "France"),
    "mos": ("Army", "Russia"),
    "mun": ("Army", "Germany"),
    "nap": ("Fleet", "Italy"),
    "par": ("Army", "France"),
    "rom": ("Army", "Italy"),
    "sev": ("Fleet", "Russia"),
    "smy": ("Army", "Turkey"),
    "stp/sc": ("Fleet", "Russia"),
    "tri": ("Fleet", "Austria"),
    "ven": ("Army", "Italy"),
    "vie": ("Army", "Austria"),
    "war": ("Army", "Russia"),
}

STARTING_SUPPLY_CENTERS = {
    "ank": "Turkey",
    "ber": "Germany",
    "bre": "France",
    "bud": "Austria",
    "con": "Turkey",
    "edi": "England",
    "kie": "Germany",
    "lon": "England",
    "lvp": "England",
    "mar": "France",
    "mos": "Russia",
    "mun": "Germany",
    "nap": "Italy",
    "par": "France",
    "rom": "Italy",
    "sev": "Russia",
    "smy": "Turkey",
    "stp": "Russia",
    "tri": "Austria",
    "ven": "Italy",
    "vie": "Austria",
    "war": "Russia",
}

# Phase 1: Spring 1901 orders
PHASE1_ORDERS = {
    "England": [
        ("edi", OrderType.MOVE, "nrg", None),
        ("lvp", OrderType.MOVE, "yor", None),
        ("lon", OrderType.MOVE, "eng", None),
    ],
    "France": [
        ("bre", OrderType.MOVE, "eng", None),
        ("par", OrderType.MOVE, "bur", None),
        ("mar", OrderType.MOVE, "spa", None),
    ],
    "Germany": [
        ("kie", OrderType.MOVE, "den", None),
        ("ber", OrderType.MOVE, "kie", None),
        ("mun", OrderType.MOVE, "ruh", None),
    ],
    "Italy": [
        ("nap", OrderType.MOVE, "ion", None),
        ("rom", OrderType.MOVE, "apu", None),
        ("ven", OrderType.MOVE, "tyr", None),
    ],
    "Austria": [
        ("tri", OrderType.MOVE, "adr", None),
        ("bud", OrderType.MOVE, "ser", None),
        ("vie", OrderType.MOVE, "gal", None),
    ],
    "Turkey": [
        ("ank", OrderType.MOVE, "bla", None),
        ("con", OrderType.MOVE, "bul", None),
        ("smy", OrderType.MOVE, "arm", None),
    ],
    "Russia": [
        ("sev", OrderType.MOVE, "bla", None),
        ("mos", OrderType.MOVE, "ukr", None),
        ("war", OrderType.MOVE, "sil", None),
        ("stp/sc", OrderType.MOVE, "bot", None),
    ],
}

# Phase 1 resolutions: most succeed, some bounce
PHASE1_BOUNCES = {"bre", "ank", "sev"}

# Phase 2: Fall 1901 units (post-Spring positions)
PHASE2_UNITS = {
    "nrg": ("Fleet", "England"),
    "yor": ("Army", "England"),
    "eng": ("Fleet", "England"),
    "bre": ("Fleet", "France"),  # bounced, stayed
    "bur": ("Army", "France"),
    "spa": ("Army", "France"),
    "den": ("Fleet", "Germany"),
    "kie": ("Army", "Germany"),  # ber->kie succeeded
    "ruh": ("Army", "Germany"),
    "ion": ("Fleet", "Italy"),
    "apu": ("Army", "Italy"),
    "tyr": ("Army", "Italy"),
    "adr": ("Fleet", "Austria"),
    "ser": ("Army", "Austria"),
    "gal": ("Army", "Austria"),
    "ank": ("Fleet", "Turkey"),  # bounced, stayed
    "bul": ("Army", "Turkey"),
    "arm": ("Army", "Turkey"),
    "sev": ("Fleet", "Russia"),  # bounced, stayed
    "ukr": ("Army", "Russia"),
    "sil": ("Army", "Russia"),
    "bot": ("Fleet", "Russia"),
}

# Phase 2: Fall 1901 orders
PHASE2_ORDERS = {
    "England": [
        ("nrg", OrderType.MOVE, "nwy", None),
        ("yor", OrderType.MOVE, "lon", None),
        ("eng", OrderType.HOLD, None, None),
    ],
    "France": [
        ("bre", OrderType.MOVE, "mid", None),
        ("bur", OrderType.HOLD, None, None),
        ("spa", OrderType.HOLD, None, None),
    ],
    "Germany": [
        ("den", OrderType.HOLD, None, None),
        ("kie", OrderType.MOVE, "hol", None),
        ("ruh", OrderType.MOVE, "bel", None),
    ],
    "Italy": [
        ("ion", OrderType.MOVE, "tun", None),
        ("apu", OrderType.MOVE, "ven", None),
        ("tyr", OrderType.MOVE, "mun", None),
    ],
    "Austria": [
        ("adr", OrderType.MOVE, "tri", None),
        ("ser", OrderType.HOLD, None, None),
        ("gal", OrderType.MOVE, "rum", None),
    ],
    "Turkey": [
        ("ank", OrderType.MOVE, "bla", None),
        ("bul", OrderType.MOVE, "gre", None),
        ("arm", OrderType.MOVE, "sev", None),
    ],
    "Russia": [
        ("sev", OrderType.HOLD, None, None),
        ("ukr", OrderType.MOVE, "rum", None),
        ("sil", OrderType.MOVE, "mun", None),
        ("bot", OrderType.MOVE, "swe", None),
    ],
}

# Phase 2 resolutions: bounces for arm->sev, ukr->rum, sil->mun
PHASE2_BOUNCES = {"arm", "ukr", "sil"}

# Phase 3: Spring 1902 units (post-Fall positions)
PHASE3_UNITS = {
    "nwy": ("Fleet", "England"),
    "lon": ("Army", "England"),
    "eng": ("Fleet", "England"),
    "mid": ("Fleet", "France"),
    "bur": ("Army", "France"),
    "spa": ("Army", "France"),
    "den": ("Fleet", "Germany"),
    "hol": ("Army", "Germany"),
    "bel": ("Army", "Germany"),
    "tun": ("Fleet", "Italy"),
    "ven": ("Army", "Italy"),
    "mun": ("Army", "Italy"),
    "tri": ("Fleet", "Austria"),
    "ser": ("Army", "Austria"),
    "rum": ("Army", "Austria"),
    "bla": ("Fleet", "Turkey"),
    "gre": ("Army", "Turkey"),
    "arm": ("Army", "Turkey"),  # bounced, stayed
    "sev": ("Fleet", "Russia"),
    "ukr": ("Army", "Russia"),  # bounced, stayed
    "sil": ("Army", "Russia"),  # bounced, stayed
    "swe": ("Fleet", "Russia"),
}

# Phase 3 supply centers (after Fall 1901 adjustments)
PHASE3_SUPPLY_CENTERS = {
    **STARTING_SUPPLY_CENTERS,
    "nwy": "England",
    "hol": "Germany",
    "bel": "Germany",
    "tun": "Italy",
    "mun": "Italy",
    "rum": "Austria",
    "gre": "Turkey",
    "bla": "Turkey",  # not an SC, will be filtered
    "swe": "Russia",
}

CHAT_MESSAGES = [
    ("france", "I think we should work together against Germany this year."),
    ("england", "Agreed. I'll move to the Channel to support you."),
    ("france", "Perfect. I'll hold in Burgundy to block any German advance."),
    ("england", "What about Italy? Can we trust them?"),
    ("france", "I've been talking to Isabella. She seems focused on Austria."),
    ("england", "Good. Let's coordinate our Fall moves after we see the results."),
]


class Command(BaseCommand):
    def handle(self, *args, **options):
        self._cleanup()
        variant = Variant.objects.get(id="classical")
        province_lookup = {p.province_id: p for p in variant.provinces.all()}
        nation_lookup = {n.name: n for n in variant.nations.all()}

        users = self._create_users()
        england_user = users["england"]

        members1, game1 = self._create_game1(
            variant, province_lookup, nation_lookup, users
        )
        self._create_game2(variant, province_lookup, nation_lookup, users)
        self._create_game3(variant, users)

        channel = self._create_chat(game1, members1)

        phase2 = Phase.objects.get(game=game1, ordinal=2)
        phase3 = Phase.objects.get(game=game1, ordinal=3)

        refresh = RefreshToken.for_user(england_user)
        self.stdout.write(
            json.dumps(
                {
                    "accessToken": str(refresh.access_token),
                    "refreshToken": str(refresh),
                    "email": f"{SCREENSHOT_EMAIL_PREFIX}england{SCREENSHOT_EMAIL_SUFFIX}",
                    "name": "Catherine de Medici",
                    "game1Id": game1.id,
                    "phase2Id": phase2.id,
                    "phase3Id": phase3.id,
                    "channelId": str(channel.id),
                }
            )
        )

    def _cleanup(self):
        AuthUser.objects.filter(
            email__startswith=SCREENSHOT_EMAIL_PREFIX,
            email__endswith=SCREENSHOT_EMAIL_SUFFIX,
        ).delete()
        Game.objects.filter(name__startswith=SCREENSHOT_GAME_PREFIX).delete()

    def _create_users(self):
        users = {}
        for user_data in USERS:
            email = f"{SCREENSHOT_EMAIL_PREFIX}{user_data['key']}{SCREENSHOT_EMAIL_SUFFIX}"
            user, _ = AuthUser.objects.get_or_create(
                email=email,
                defaults={
                    "username": email.split("@")[0],
                    "password": "unused",
                },
            )
            UserProfile.objects.update_or_create(
                user=user,
                defaults={"name": user_data["name"]},
            )
            users[user_data["key"]] = user
        return users

    def _create_members(self, game, nation_lookup, users, nation_keys=None):
        members = {}
        for user_data in USERS:
            if nation_keys and user_data["key"] not in nation_keys:
                continue
            nation = nation_lookup.get(user_data["nation"]) if nation_keys is None or user_data["key"] in nation_keys else None
            member = Member.objects.create(
                user=users[user_data["key"]],
                game=game,
                nation=nation,
            )
            members[user_data["key"]] = member
        return members

    def _create_members_pending(self, game, users, keys):
        members = {}
        for key in keys:
            member = Member.objects.create(
                user=users[key],
                game=game,
                nation=None,
            )
            members[key] = member
        return members

    def _create_units(self, phase, province_lookup, nation_lookup, unit_map):
        units = []
        for prov_id, (unit_type, nation_name) in unit_map.items():
            province = province_lookup[prov_id]
            nation = nation_lookup[nation_name]
            u_type = UnitType.ARMY if unit_type == "Army" else UnitType.FLEET
            units.append(Unit(phase=phase, province=province, nation=nation, type=u_type))
        Unit.objects.bulk_create(units)

    def _create_supply_centers(self, phase, province_lookup, nation_lookup, sc_map):
        scs = []
        for prov_id, nation_name in sc_map.items():
            province = province_lookup.get(prov_id)
            if province is None or not province.supply_center:
                continue
            nation = nation_lookup[nation_name]
            scs.append(SupplyCenter(phase=phase, province=province, nation=nation))
        SupplyCenter.objects.bulk_create(scs)

    def _create_orders(self, phase, members, province_lookup, nation_lookup, order_map, bounce_sources):
        nation_to_key = {ud["nation"]: ud["key"] for ud in USERS}
        resolutions = []

        for nation_name, orders in order_map.items():
            key = nation_to_key[nation_name]
            member = members[key]
            phase_state = phase.phase_states.get(member=member)

            for source_id, order_type, target_id, aux_id in orders:
                source = province_lookup[source_id]
                target = province_lookup.get(target_id) if target_id else None
                aux = province_lookup.get(aux_id) if aux_id else None

                order = Order.objects.create(
                    phase_state=phase_state,
                    source=source,
                    order_type=order_type,
                    target=target,
                    aux=aux,
                )

                status = (
                    OrderResolutionStatus.BOUNCED
                    if source_id in bounce_sources
                    else OrderResolutionStatus.SUCCEEDED
                )
                resolutions.append(OrderResolution(order=order, status=status))

        OrderResolution.objects.bulk_create(resolutions)

    def _create_phase_states(self, phase, members, has_possible_orders=False, orders_confirmed=False):
        for member in members.values():
            phase.phase_states.create(
                member=member,
                has_possible_orders=has_possible_orders,
                orders_confirmed=orders_confirmed,
            )

    def _create_game1(self, variant, province_lookup, nation_lookup, users):
        game = Game.objects.create(
            variant=variant,
            name=f"{SCREENSHOT_GAME_PREFIX} The Great War",
            status=GameStatus.ACTIVE,
            deadline_mode=DeadlineMode.DURATION,
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        )
        members = self._create_members(game, nation_lookup, users)

        # Phase 1: Spring 1901 Movement (COMPLETED)
        phase1 = Phase.objects.create(
            game=game,
            variant=variant,
            season="Spring",
            year=1901,
            type="Movement",
            ordinal=1,
            status=PhaseStatus.COMPLETED,
        )
        self._create_units(phase1, province_lookup, nation_lookup, STARTING_UNITS)
        self._create_supply_centers(phase1, province_lookup, nation_lookup, STARTING_SUPPLY_CENTERS)
        self._create_phase_states(phase1, members)
        self._create_orders(phase1, members, province_lookup, nation_lookup, PHASE1_ORDERS, PHASE1_BOUNCES)

        # Phase 2: Fall 1901 Movement (COMPLETED)
        phase2 = Phase.objects.create(
            game=game,
            variant=variant,
            season="Fall",
            year=1901,
            type="Movement",
            ordinal=2,
            status=PhaseStatus.COMPLETED,
        )
        self._create_units(phase2, province_lookup, nation_lookup, PHASE2_UNITS)
        self._create_supply_centers(phase2, province_lookup, nation_lookup, STARTING_SUPPLY_CENTERS)
        self._create_phase_states(phase2, members)
        self._create_orders(phase2, members, province_lookup, nation_lookup, PHASE2_ORDERS, PHASE2_BOUNCES)

        # Phase 3: Spring 1902 Movement (ACTIVE)
        empty_options = {ud["nation"]: {} for ud in USERS}
        phase3 = Phase.objects.create(
            game=game,
            variant=variant,
            season="Spring",
            year=1902,
            type="Movement",
            ordinal=3,
            status=PhaseStatus.ACTIVE,
            scheduled_resolution=timezone.now() + timedelta(days=365),
            options=empty_options,
        )
        self._create_units(phase3, province_lookup, nation_lookup, PHASE3_UNITS)
        self._create_supply_centers(phase3, province_lookup, nation_lookup, PHASE3_SUPPLY_CENTERS)
        self._create_phase_states(phase3, members, has_possible_orders=True, orders_confirmed=False)

        return members, game

    def _create_game2(self, variant, province_lookup, nation_lookup, users):
        game = Game.objects.create(
            variant=variant,
            name=f"{SCREENSHOT_GAME_PREFIX} Mediterranean Alliance",
            status=GameStatus.ACTIVE,
            deadline_mode=DeadlineMode.DURATION,
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        )
        self._create_members(game, nation_lookup, users)
        members = {
            ud["key"]: game.members.get(user__email=f"{SCREENSHOT_EMAIL_PREFIX}{ud['key']}{SCREENSHOT_EMAIL_SUFFIX}")
            for ud in USERS
        }

        empty_options = {ud["nation"]: {} for ud in USERS}
        phase = Phase.objects.create(
            game=game,
            variant=variant,
            season="Spring",
            year=1901,
            type="Movement",
            ordinal=1,
            status=PhaseStatus.ACTIVE,
            scheduled_resolution=timezone.now() + timedelta(days=365),
            options=empty_options,
        )
        self._create_units(phase, province_lookup, nation_lookup, STARTING_UNITS)
        self._create_supply_centers(phase, province_lookup, nation_lookup, STARTING_SUPPLY_CENTERS)
        self._create_phase_states(phase, members, has_possible_orders=True, orders_confirmed=False)

        return game

    def _create_game3(self, variant, users):
        game = Game.objects.create(
            variant=variant,
            name=f"{SCREENSHOT_GAME_PREFIX} North Sea Gambit",
            status=GameStatus.PENDING,
            deadline_mode=DeadlineMode.DURATION,
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        )
        self._create_members_pending(game, users, ["england", "france", "germany"])
        return game

    def _create_chat(self, game, members):
        england_member = members["england"]
        france_member = members["france"]

        channel = Channel.objects.create(
            name="England, France",
            private=True,
            game=game,
        )
        ChannelMember.objects.create(member=england_member, channel=channel)
        ChannelMember.objects.create(member=france_member, channel=channel)

        member_map = {"england": england_member, "france": france_member}
        for sender_key, body in CHAT_MESSAGES:
            ChannelMessage.objects.create(
                channel=channel,
                sender=member_map[sender_key],
                body=body,
            )

        return channel
