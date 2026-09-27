import random
from datetime import time

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q

from agent.orders import option_to_selected
from channel.models import Channel, ChannelMessage
from common.constants import (
    CommitmentRequirement,
    DeadlineMode,
    GameStatus,
    MemberKind,
    MovementPhaseDuration,
    OrderType,
    PhaseFrequency,
    PhaseType,
    PressType,
    UserKind,
)
from draw_proposal.models import DrawProposal
from emit import emit
from game.models import Game
from harness.adapter import orders_to_options
from login.models import AuthUser
from member.models import Member
from notification.models import Notification
from order.models import Order
from order.utils import flatten_options
from phase.models import Phase
from supply_center.models import SupplyCenter
from user_profile.models import UserProfile
from variant.models import Variant

TESTER_EMAIL = "staging-tester@example.com"
TESTER_NAME = "Staging Tester"
BOT_EMAIL = "staging-bot@example.com"
BOT_NAME = "Staging Bot"
PLAYER_NAMES = [
    "Alice Moreau",
    "Bruno Keller",
    "Chiara Rossi",
    "Dmitri Volkov",
    "Emre Yilmaz",
    "Fiona Hale",
    "Gustav Lind",
    "Hana Novak",
]


class Command(BaseCommand):
    help = "Seeds a login user, opponents and games in a range of states for testing the web app on staging"

    def add_arguments(self, parser):
        parser.add_argument("--password", type=str, default="password")
        parser.add_argument("--skip-if-seeded", action="store_true")

    def handle(self, *args, **options):
        if not (settings.DEBUG or settings.ENVIRONMENT == "staging"):
            raise CommandError("seed_staging only runs with DEBUG=True or ENVIRONMENT=staging")

        if options["skip_if_seeded"] and AuthUser.objects.filter(email=TESTER_EMAIL).exists():
            self.stdout.write(f"{TESTER_EMAIL} already exists; skipping.")
            return

        password = options["password"]
        self.rng = random.Random(0)
        password_hash = make_password(password)
        self.tester = self._user(TESTER_EMAIL, TESTER_NAME, password_hash)
        self.players = [
            self._user(f"staging-player-{index}@example.com", name, password_hash)
            for index, name in enumerate(PLAYER_NAMES, start=1)
        ]
        self.bot = self._user(BOT_EMAIL, BOT_NAME, make_password(None), kind=UserKind.DUMBBOT)
        self._clear()

        self.classical = Variant.objects.with_game_creation_data().get(id="classical")
        self.italy_vs_germany = Variant.objects.with_game_creation_data().get(id="italy-vs-germany")

        scenarios = [
            self._seed_finished_solo_win,
            self._seed_finished_solo_loss,
            self._seed_finished_draw,
            self._seed_finished_abandoned,
            self._seed_active_tester_in_civil_disorder,
            self._seed_active_tester_missed_deadline,
            self._seed_active_player_in_civil_disorder,
            self._seed_active_replaceable_seat,
            self._seed_active_tester_eliminated,
            self._seed_active_retreat,
            self._seed_active_adjustment,
            self._seed_active_mid_game,
            self._seed_active_draw_proposed,
            self._seed_active_orders_required,
            self._seed_active_orders_not_confirmed,
            self._seed_active_orders_confirmed,
            self._seed_active_paused,
            self._seed_pending_created,
            self._seed_pending_game_master,
            self._seed_pending_joined,
            self._seed_open_one_seat_left,
            self._seed_open_committed,
            self._seed_open_gunboat,
            self._seed_sandbox,
        ]
        for scenario in scenarios:
            game = scenario()
            game.refresh_from_db()
            self.stdout.write(f"  {game.status:<10} {game.name} ({game.id})")

        self.tester.profile.refresh_from_db()
        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(scenarios)} games. Log in as {TESTER_EMAIL} / {password} "
                f"(commitment: {self.tester.profile.commitment})"
            )
        )

    def _user(self, email, name, password_hash, kind=UserKind.HUMAN):
        user, _ = AuthUser.objects.get_or_create(email=email, defaults={"username": email.split("@")[0]})
        user.is_active = True
        user.password = password_hash
        user.save()
        UserProfile.objects.update_or_create(user=user, defaults={"name": name, "kind": kind})
        return user

    def _clear(self):
        users = [self.tester, *self.players, self.bot]
        game_ids = set(
            Game.objects.filter(
                Q(members__user__in=users) | Q(created_by__in=users) | Q(game_master__in=users)
            ).values_list("id", flat=True)
        )
        Member.objects.filter(game_id__in=game_ids, replaced_by__isnull=False).update(nation=None)
        Game.objects.filter(id__in=game_ids).delete()
        Notification.objects.filter(recipient__in=users).delete()

    def _game(self, name, *, creator, players, variant=None, as_game_master=False, **kwargs):
        kwargs.setdefault("deadline_mode", DeadlineMode.DURATION)
        kwargs.setdefault("movement_phase_duration", MovementPhaseDuration.TWO_WEEKS)
        with transaction.atomic():
            game = Game.objects.create_from_template(
                variant or self.classical,
                name=name,
                created_by=creator,
                game_master=creator if as_game_master else None,
                admin=creator,
                **kwargs,
            )
            game.channels.create(name="Public Press", private=False)
            if as_game_master:
                game.seat(creator, kind=MemberKind.GAME_MASTER)
            for user in players:
                game.seat(user)
        return game

    def _start(self, game, nations=None):
        for user, nation_name in (nations or {}).items():
            Member.objects.assign_nation(self._member(game, user), game.variant.nations.get(name=nation_name))
        game.start()
        return game

    def _member(self, game, user):
        return game.members.players().select_related("nation", "user").get(user=user, replaced_by__isnull=True)

    def _order(self, phase, user, selected, lookup=None):
        order = Order.objects.create_from_selected(user, phase, selected, province_lookup=lookup)
        Order.objects.delete_existing_for_source(order.phase_state, order.source)
        order.save()

    def _random_orders(self, phase, phase_state, lookup):
        member = phase_state.member
        options = orders_to_options(flatten_options(phase.transformed_options.get(member.nation.name, {}), lookup))
        by_source = {}
        for option in options:
            by_source.setdefault(option["source"], []).append(option)
        sources = sorted(by_source)
        if phase.type == PhaseType.ADJUSTMENT:
            sources = self.rng.sample(sources, min(len(sources), phase_state.max_allowed_adjustment_orders()))
        for source in sources:
            choices = by_source[source]
            moves = [option for option in choices if option["order_type"] == OrderType.MOVE]
            option = self.rng.choice(moves if moves and self.rng.random() < 0.7 else choices)
            self._order(phase, member.user, option_to_selected(option), lookup)

    def _advance(self, game, orders=None, nmr=(), random_orders=True):
        phase = game.current_phase
        lookup = {province.province_id: province for province in phase.variant.provinces.all()}
        orders_by_user_id = {user.id: selections for user, selections in (orders or {}).items()}
        nmr_user_ids = {user.id for user in nmr}
        for phase_state in phase.phase_states.select_related("member__nation", "member__user"):
            member = phase_state.member
            if not phase_state.has_possible_orders or member.civil_disorder or member.user_id in nmr_user_ids:
                continue
            if member.user_id in orders_by_user_id:
                for selected in orders_by_user_id[member.user_id]:
                    self._order(phase, member.user, selected, lookup)
            elif random_orders:
                self._random_orders(phase, phase_state, lookup)
            phase_state.orders_confirmed = True
            phase_state.save(update_fields=["orders_confirmed", "updated_at"])
        Phase.objects.resolve(phase)

    def _advance_to(self, game, season, year, nmr=(), random_orders=True):
        while game.status == GameStatus.ACTIVE:
            phase = game.current_phase
            if phase.season == season and phase.year == year and phase.type == PhaseType.MOVEMENT:
                return
            self._advance(game, nmr=nmr, random_orders=random_orders)

    def _confirm(self, game, users):
        game.current_phase.phase_states.filter(member__user__in=users).update(orders_confirmed=True)

    def _message(self, channel, user, body):
        game = channel.game
        message = ChannelMessage.objects.create(
            channel=channel,
            sender=self._member(game, user),
            phase=game.current_phase,
            body=body,
        )
        emit("channel_message", message=message)

    def _civil_disorder(self, game, users):
        self._advance_to(game, "Spring", 1902, nmr=users, random_orders=False)

    def _give_supply_centers(self, game, user, count):
        member = self._member(game, user)
        phase = game.current_phase
        owned = phase.supply_centers.filter(nation=member.nation).count()
        missing = count - owned
        neutral = game.variant.provinces.filter(supply_center=True, parent__isnull=True).exclude(
            id__in=phase.supply_centers.values("province_id")
        )
        SupplyCenter.objects.bulk_create(
            [SupplyCenter(phase=phase, nation=member.nation, province=province) for province in neutral[:missing]]
        )
        missing = count - phase.supply_centers.filter(nation=member.nation).count()
        if missing > 0:
            taken = phase.supply_centers.exclude(nation=member.nation).values_list("id", flat=True)[:missing]
            SupplyCenter.objects.filter(id__in=list(taken)).update(nation=member.nation)

    def _eliminate(self, game, user, successor):
        member = self._member(game, user)
        phase = game.current_phase
        phase.units.filter(nation=member.nation).delete()
        phase.supply_centers.filter(nation=member.nation).update(nation=self._member(game, successor).nation)

    def _seed_finished_solo_win(self):
        game = self._game("Finished: you won solo", creator=self.tester, players=[self.tester, *self.players[:6]])
        self._start(game, {self.tester: "France"})
        self._give_supply_centers(game, self.tester, game.variant.solo_victory_supply_centers)
        self._advance(game)
        return game

    def _seed_finished_solo_loss(self):
        game = self._game(
            "Finished: another player won solo", creator=self.players[0], players=[self.tester, *self.players[:6]]
        )
        self._start(game, {self.players[0]: "Turkey"})
        self._give_supply_centers(game, self.players[0], game.variant.solo_victory_supply_centers)
        self._advance(game)
        return game

    def _seed_finished_draw(self):
        game = self._game("Finished: five-way draw", creator=self.tester, players=[self.tester, *self.players[:6]])
        self._start(game)
        self._civil_disorder(game, self.players[4:6])
        proposal = DrawProposal.objects.create_proposal(game=game, created_by=self._member(game, self.tester))
        proposal.votes.filter(accepted__isnull=True).update(accepted=True)
        proposal.process_acceptance()
        return game

    def _seed_finished_abandoned(self):
        players = [self.tester, *self.players[:6]]
        game = self._game("Finished: abandoned", creator=self.tester, players=players, private=True)
        self._start(game)
        self._civil_disorder(game, players)
        return game

    def _seed_active_tester_in_civil_disorder(self):
        game = self._game(
            "Active: you are in civil disorder",
            creator=self.players[0],
            players=[self.tester, *self.players[:6]],
            private=True,
        )
        self._start(game)
        self._civil_disorder(game, [self.tester])
        return game

    def _seed_active_tester_missed_deadline(self):
        game = self._game(
            "Active: you missed the last deadline",
            creator=self.players[1],
            players=[self.tester, *self.players[:6]],
            private=True,
        )
        self._start(game)
        self._advance(game, nmr=[self.tester])
        return game

    def _seed_active_player_in_civil_disorder(self):
        game = self._game(
            "Active: players in civil disorder", creator=self.tester, players=[self.tester, *self.players[:6]]
        )
        self._start(game)
        self._civil_disorder(game, self.players[1:3])
        Member.objects.hand_over_seat(self._member(game, self.players[2]), self.players[6])
        return game

    def _seed_active_replaceable_seat(self):
        game = self._game("Active: take over an abandoned seat", creator=self.players[0], players=self.players[:7])
        self._start(game)
        self._civil_disorder(game, [self.players[3]])
        return game

    def _seed_active_tester_eliminated(self):
        game = self._game(
            "Active: you were eliminated", creator=self.players[0], players=[self.tester, *self.players[:6]]
        )
        self._start(game, {self.tester: "Italy", self.players[0]: "Austria"})
        self._eliminate(game, self.tester, self.players[0])
        self._advance(game, orders={self.tester: []})
        return game

    def _seed_active_retreat(self):
        austria = self.players[0]
        game = self._game("Active: retreat phase", creator=self.tester, players=[self.tester, *self.players[:6]])
        self._start(game, {self.tester: "Italy", austria: "Austria"})
        self._advance(game, orders={austria: [["vie", OrderType.MOVE, "tyr"]]}, random_orders=False)
        self._advance(
            game,
            orders={austria: [["tri", OrderType.MOVE, "ven"], ["tyr", OrderType.SUPPORT, "tri", "ven"]]},
            random_orders=False,
        )
        return game

    def _seed_active_adjustment(self):
        game = self._game("Active: adjustment phase", creator=self.tester, players=[self.tester, *self.players[:6]])
        self._start(game, {self.tester: "Germany"})
        self._advance(
            game,
            orders={
                self.tester: [
                    ["kie", OrderType.MOVE, "den"],
                    ["mun", OrderType.MOVE, "ruh"],
                    ["ber", OrderType.MOVE, "kie"],
                ]
            },
            random_orders=False,
        )
        self._advance(game, orders={self.tester: [["ruh", OrderType.MOVE, "hol"]]}, random_orders=False)
        return game

    def _seed_active_mid_game(self):
        game = self._game(
            "Active: mid-game with messages",
            creator=self.players[0],
            players=[self.tester, *self.players[:6]],
            nmr_extensions_allowed=2,
        )
        self._start(game)
        public_press = game.get_public_press()
        self._message(public_press, self.players[0], "Good luck everyone, may the best diplomat win.")
        self._message(public_press, self.tester, "Likewise! Looking forward to a clean game.")
        self._advance_to(game, "Fall", 1902)
        channel = Channel.objects.create_from_member_ids(
            self.tester,
            [self._member(game, user).id for user in self.players[1:3]],
            game,
            title="Western alliance",
        )
        self._message(channel, self.players[1], "Shall we coordinate against the east this year?")
        self._message(channel, self.players[2], "I'm in. Can you support me into Munich?")
        self._message(public_press, self.players[3], "Anyone interested in a ceasefire in the Balkans?")
        self._confirm(game, self.players[:3])
        return game

    def _seed_active_draw_proposed(self):
        game = self._game("Active: draw proposed", creator=self.players[0], players=[self.tester, *self.players[:6]])
        self._start(game)
        self._advance(game)
        rejected = DrawProposal.objects.create_proposal(game=game, created_by=self._member(game, self.players[3]))
        rejected.votes.filter(member__user=self.players[4]).update(accepted=False)
        proposal = DrawProposal.objects.create_proposal(game=game, created_by=self._member(game, self.players[0]))
        proposal.votes.filter(member__user__in=self.players[1:3]).update(accepted=True)
        return game

    def _seed_active_orders_required(self):
        game = self._game(
            "Active: orders required", creator=self.tester, players=[self.tester, *self.players[:5], self.bot]
        )
        return self._start(game)

    def _seed_active_orders_not_confirmed(self):
        game = self._game(
            "Active: orders not confirmed",
            creator=self.players[1],
            players=[self.tester, *self.players[:6]],
            anonymous=True,
        )
        self._start(game, {self.tester: "England"})
        phase = game.current_phase
        self._order(phase, self.tester, ["lon", OrderType.MOVE, "nth"])
        self._order(phase, self.tester, ["edi", OrderType.MOVE, "nrg"])
        return game

    def _seed_active_orders_confirmed(self):
        game = self._game(
            "Active: orders confirmed",
            creator=self.players[2],
            players=[self.tester, *self.players[:6]],
            press_type=PressType.NO_PRESS,
        )
        self._start(game, {self.tester: "Russia"})
        phase = game.current_phase
        self._order(phase, self.tester, ["war", OrderType.MOVE, "gal"])
        self._order(phase, self.tester, ["sev", OrderType.MOVE, "bla"])
        self._confirm(game, [self.tester, *self.players[:3]])
        return game

    def _seed_active_paused(self):
        game = self._game("Active: paused", creator=self.tester, players=[self.tester, *self.players[:6]])
        self._start(game)
        game.pause()
        emit("game_paused", game=game, actor=self.tester)
        return game

    def _seed_pending_created(self):
        game = self._game("Pending: waiting for players", creator=self.tester, players=[self.tester, *self.players[:3]])
        Member.objects.set_nation_preferences(
            self._member(game, self.tester),
            [game.variant.nations.get(name=name) for name in ("France", "England", "Germany")],
        )
        return game

    def _seed_pending_game_master(self):
        return self._game(
            "Pending: you are the game master",
            creator=self.tester,
            players=self.players[:3],
            as_game_master=True,
        )

    def _seed_pending_joined(self):
        return self._game(
            "Pending: joined another player's game",
            creator=self.players[3],
            players=[self.players[3], self.players[4], self.tester],
        )

    def _seed_open_one_seat_left(self):
        return self._game("Open: one seat left", creator=self.players[0], players=self.players[:6])

    def _seed_open_committed(self):
        return self._game(
            "Open: committed players only",
            creator=self.players[0],
            players=[self.players[0], self.players[6]],
            commitment_requirement=CommitmentRequirement.COMMITTED,
        )

    def _seed_open_gunboat(self):
        return self._game(
            "Open: gunboat Italy vs Germany",
            creator=self.players[7],
            players=[self.players[7]],
            variant=self.italy_vs_germany,
            press_type=PressType.NO_PRESS,
            deadline_mode=DeadlineMode.FIXED_TIME,
            movement_phase_duration=None,
            fixed_deadline_time=time(20, 0),
            fixed_deadline_timezone="Europe/London",
            movement_frequency=PhaseFrequency.DAILY,
        )

    def _seed_sandbox(self):
        return Game.objects.create_sandbox(self.tester, name="Sandbox: practice game", variant=self.classical)
