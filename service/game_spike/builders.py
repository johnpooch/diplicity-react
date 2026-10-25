from channel.models import Channel, ChannelMember
from common.builders import Builder
from common.constants import PhaseStatus

from .models import Game, Member, Phase, SupplyCenter, Unit


class GameBuilder(Builder):
    @classmethod
    def from_template(cls, variant, seats=(), **fields):
        template = Phase.objects.prefetch_related("units", "supply_centers").get(
            variant=variant, game__isnull=True, status=PhaseStatus.TEMPLATE
        )
        return cls(source=template, variant=variant, seats=seats, **fields).run()

    @classmethod
    def from_phase(cls, phase, seats=(), **fields):
        return cls(source=phase, variant=phase.game.variant, seats=seats, **fields).run()

    def build(self):
        source = self.fields.pop("source")
        seats = self.fields.pop("seats")
        game = Game.objects.create(**self.fields)
        phase = Phase.objects.create(
            game=game,
            variant=game.variant,
            season=source.season,
            year=source.year,
            type=source.type,
            status=PhaseStatus.PENDING,
            ordinal=1,
        )
        Unit.objects.bulk_create(
            Unit(
                phase=phase,
                type=unit.type,
                nation_id=unit.nation_id,
                province_id=unit.province_id,
                dislodged=unit.dislodged,
                dislodged_from_id=unit.dislodged_from_id,
            )
            for unit in source.units.all()
        )
        SupplyCenter.objects.bulk_create(
            SupplyCenter(phase=phase, nation_id=center.nation_id, province_id=center.province_id)
            for center in source.supply_centers.all()
        )
        members = Member.objects.bulk_create(Member(game=game, sandbox=game.sandbox, **seat) for seat in seats)
        if not game.sandbox:
            channel = Channel.objects.create(game_id=game.pk, name="Public Press", private=False)
            ChannelMember.objects.bulk_create(ChannelMember(channel=channel, member_id=member.pk) for member in members)
        return game
