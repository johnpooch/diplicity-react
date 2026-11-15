from django.db.models import Count

from common.constants import CommitmentBand, GameStatus, PlayerName
from common.loaders import Hydrator
from report.checks import HasNotReportedCheck
from report.policies import CanModerateGamePolicy, CanReportPolicy
from supply_center.models import SupplyCenter
from unit.models import Unit

from .models import Member


def is_current_user(member, actor):
    return (
        member.user_id is not None
        and actor.is_authenticated
        and member.user_id == actor.pk
    )


class MemberVisibilityHydrator(Hydrator):
    def hydrate(self, members, actor):
        moderated = {}
        for member in members:
            game = member.game
            current = is_current_user(member, actor)
            masked = (
                game.anonymity_active
                and not member.is_game_master
                and not member.is_bot
                and not current
                and not self.moderates(game, actor, moderated)
            )
            visible = not masked and member.user_id is not None
            member.is_current_user = current
            member.visible_user_id = member.user_id if visible else None
            member.visible_name = PlayerName.ANONYMOUS if masked else member.name
            member.visible_picture_path = (
                member.user.profile.picture_path if visible else None
            )
            member.visible_is_game_creator = (
                visible and member.user_id == game.created_by_id
            )
            member.visible_is_admin = visible and member.user_id == game.admin_id

    def moderates(self, game, actor, moderated):
        if game.id not in moderated:
            moderated[game.id] = CanModerateGamePolicy.decide(game, actor).allowed
        return moderated[game.id]


class MemberCommitmentHydrator(Hydrator):
    def hydrate(self, members, actor):
        Member.objects.hydrate_commitment_totals(members)
        for member in members:
            shown = (
                member.user is not None
                and not member.is_bot
                and not member.game.anonymous
            )
            member.public_commitment_total = (
                member.commitment_total if shown else None
            )
            member.public_commitment_band = (
                CommitmentBand.for_total(member.commitment_total) if shown else None
            )


class NationPreferenceIdsHydrator(Hydrator):
    def hydrate(self, members, actor):
        for member in members:
            member.visible_nation_preference_ids = (
                [
                    preference.nation.nation_id
                    for preference in member.nation_preferences.all()
                ]
                if is_current_user(member, actor)
                else []
            )


class NationPreferencesHydrator(Hydrator):
    def hydrate(self, members, actor):
        for member in members:
            member.visible_nation_preferences = (
                [preference.nation.name for preference in member.nation_preferences.all()]
                if is_current_user(member, actor)
                and not member.is_game_master
                and member.game.status == GameStatus.PENDING
                else None
            )


class MemberActionsHydrator(Hydrator):
    def hydrate(self, members, actor):
        for member in members:
            member.viewer_actions = member.actions_for(actor)


class ReportDecisionHydrator(Hydrator):
    def hydrate(self, members, actor):
        for member in members:
            decision = CanReportPolicy.decide(member, actor)
            member.viewer_can_report = decision.allowed
            member.viewer_already_reported = (
                decision.reason == HasNotReportedCheck.reason
            )


class PieceCountsHydrator(Hydrator):
    def hydrate(self, members, actor):
        phases = {member.id: self.counted_phase(member) for member in members}
        phase_ids = {phase.id for phase in phases.values() if phase is not None}
        supply_centers = self.counts(SupplyCenter, phase_ids)
        units = self.counts(Unit, phase_ids)
        for member in members:
            phase = phases[member.id]
            key = None if phase is None else (phase.id, member.nation_id)
            member.supply_center_count = (
                None if key is None else supply_centers.get(key, 0)
            )
            member.unit_count = None if key is None else units.get(key, 0)

    def counted_phase(self, member):
        game = member.game
        if member.nation_id is None or game.status in (
            GameStatus.PENDING,
            GameStatus.MUSTERING,
        ):
            return None
        return game.current_phase

    def counts(self, model, phase_ids):
        if not phase_ids:
            return {}
        rows = (
            model.objects.filter(phase_id__in=phase_ids)
            .order_by()
            .values("phase_id", "nation_id")
            .annotate(count=Count("id"))
            .values_list("phase_id", "nation_id", "count")
        )
        return {(phase_id, nation_id): count for phase_id, nation_id, count in rows}
