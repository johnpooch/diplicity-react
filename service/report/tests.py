from datetime import timedelta

import pytest
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from channel.models import Channel, ChannelMessage
from common.actors import SYSTEM
from common.constants import GameStatus, MemberKind, OrderType
from common.policies import Refused
from order.models import Order
from report.constants import ReportDecision, ReportReason, ReportStatus
from report.checks import IsAssignedInGameCheck
from member.models import Member
from report.models import Mark, Report, ReportReview
from report.policies import CanModerateGamePolicy, ModeratorPolicy

LIST_URL = reverse("moderation-report-list")


@pytest.fixture
def moderator(user_factory):
    user = user_factory(username="moderator", name="Mia Moderator")
    user.profile.is_moderator = True
    user.profile.save()
    return user


@pytest.fixture
def moderator_client(authenticated_client_factory, moderator):
    return authenticated_client_factory(moderator)


@pytest.fixture
def report_factory(db, game_factory, member_factory):
    def _create(
        game=None,
        reason=ReportReason.ABUSE_AND_HARASSMENT,
        age=timedelta(0),
        decision=None,
        reviewed_by=None,
        review_note="Clear breach of the code of conduct.",
    ):
        game = game or game_factory()
        reporter = member_factory(game=game)
        reported = member_factory(game=game)
        report = Report.objects.create(
            reporter=reporter,
            reported=reported,
            reason=reason,
            note="Insults in press.",
        )
        Report.objects.filter(pk=report.pk).update(created_at=timezone.now() - age)
        if decision is not None:
            ReportReview.objects.create(
                report=report,
                decision=decision,
                reviewed_by=reviewed_by or reporter.user,
                note=review_note,
            )
        return report

    return _create


def _detail_url(report):
    return reverse("moderation-report-detail", args=[report.id])


def _jwt_client(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


class TestReportModel:
    @pytest.mark.django_db
    def test_status_is_pending_without_review(self, report_factory):
        report = report_factory()

        assert report.status == ReportStatus.PENDING

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "decision", [ReportDecision.APPROVED, ReportDecision.REJECTED]
    )
    def test_status_is_review_decision(self, report_factory, decision):
        report = report_factory(decision=decision)

        assert Report.objects.get(pk=report.pk).status == decision

    @pytest.mark.django_db
    def test_status_querysets_filter_by_review(self, report_factory):
        pending = report_factory()
        approved = report_factory(decision=ReportDecision.APPROVED)
        rejected = report_factory(decision=ReportDecision.REJECTED)

        assert list(Report.objects.pending()) == [pending]
        assert list(Report.objects.approved()) == [approved]
        assert list(Report.objects.rejected()) == [rejected]


class TestReportCommand:
    @pytest.mark.django_db
    def test_report_records_the_reporting_member(self, game_factory, member_factory):
        game = game_factory()
        reporter = member_factory(game=game)
        reported = member_factory(game=game)

        report = Report.objects.report(
            reported, reporter.user, ReportReason.SECRET_TEAMING, "Same IP"
        )

        assert report.reporter == reporter
        assert report.reported == reported

    @pytest.mark.django_db
    def test_report_refuses_duplicate(self, game_factory, member_factory):
        game = game_factory()
        reporter = member_factory(game=game)
        reported = member_factory(game=game)
        Report.objects.report(reported, reporter.user, ReportReason.OTHER, "Spam")

        with pytest.raises(Refused) as refused:
            Report.objects.report(reported, reporter.user, ReportReason.OTHER, "Again")

        assert refused.value.decision.reason == "already_reported"


class TestReportReasonListView:
    url = reverse("report-reason-list")

    @pytest.mark.django_db
    def test_unauthenticated(self, unauthenticated_client):
        response = unauthenticated_client.get(self.url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_returns_all_reasons_in_display_order(self, authenticated_client):
        response = authenticated_client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert [reason["key"] for reason in response.data] == [
            "abuse_and_harassment",
            "multiple_accounts",
            "secret_teaming",
            "other",
        ]
        assert response.data[0]["label"] == "Abuse and harassment"
        assert all(reason["description"] for reason in response.data)


class TestReportCreateView:
    def _url(self, member, game=None):
        game_id = member.game_id if game is None else game.id
        return reverse("game-member-report", args=[game_id, member.id])

    def _report(
        self,
        client,
        member,
        reason=ReportReason.ABUSE_AND_HARASSMENT,
        note="Insults in press.",
    ):
        return client.post(
            self._url(member), {"reason": reason, "note": note}, format="json"
        )

    @pytest.fixture
    def game(self, game_factory):
        return game_factory()

    @pytest.fixture
    def reporter(self, game, member_factory, primary_user):
        return member_factory(game=game, user=primary_user)

    @pytest.fixture
    def reported(self, game, member_factory, reporter):
        return member_factory(game=game)

    @pytest.mark.django_db
    def test_unauthenticated(self, unauthenticated_client, reported):
        response = self._report(unauthenticated_client, reported)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_creates_report(self, authenticated_client, reporter, reported):
        response = self._report(
            authenticated_client, reported, note="Called me names in press."
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["reason"] == "abuse_and_harassment"
        assert response.data["note"] == "Called me names in press."
        assert response.data["status"] == "pending"
        report = Report.objects.get()
        assert report.reporter == reporter
        assert report.reported == reported

    @pytest.mark.django_db
    def test_response_in_anonymous_game_does_not_identify_the_user(
        self, authenticated_client, game_factory, member_factory, primary_user
    ):
        game = game_factory(anonymous=True)
        member_factory(game=game, user=primary_user)
        reported = member_factory(game=game)

        response = self._report(authenticated_client, reported)

        assert response.status_code == status.HTTP_201_CREATED
        assert set(response.data) == {
            "id",
            "reported",
            "reason",
            "note",
            "status",
            "created_at",
        }
        assert response.data["reported"] == reported.id

    @pytest.mark.django_db
    def test_self_report_refused(self, authenticated_client, reporter):
        response = self._report(authenticated_client, reporter)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "own_member"
        assert Report.objects.count() == 0

    @pytest.mark.django_db
    def test_duplicate_report_refused(self, authenticated_client, reported):
        self._report(authenticated_client, reported)

        response = self._report(authenticated_client, reported)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "already_reported"
        assert Report.objects.count() == 1

    @pytest.mark.django_db
    def test_reporting_several_players_in_one_game(
        self, authenticated_client, game, reported, member_factory
    ):
        other = member_factory(game=game)

        first = self._report(authenticated_client, reported)
        second = self._report(authenticated_client, other)

        assert first.status_code == status.HTTP_201_CREATED
        assert second.status_code == status.HTTP_201_CREATED
        assert Report.objects.count() == 2

    @pytest.mark.django_db
    def test_sandbox_game_refused(
        self, authenticated_client, game_factory, member_factory, primary_user
    ):
        game = game_factory(sandbox=True)
        member_factory(game=game, user=primary_user)
        reported = member_factory(game=game)

        response = self._report(authenticated_client, reported)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "sandbox_game"

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "game_status",
        [
            GameStatus.PENDING,
            GameStatus.MUSTERING,
            GameStatus.ACTIVE,
            GameStatus.ABANDONED,
            GameStatus.COMPLETED,
        ],
    )
    def test_allowed_in_every_game_status(
        self,
        authenticated_client,
        game_factory,
        member_factory,
        primary_user,
        game_status,
    ):
        game = game_factory(status=game_status)
        member_factory(game=game, user=primary_user)
        reported = member_factory(game=game)

        response = self._report(authenticated_client, reported)

        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_non_member_refused(self, authenticated_client, game, member_factory):
        reported = member_factory(game=game)

        response = self._report(authenticated_client, reported)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "not_member"

    @pytest.mark.django_db
    def test_member_of_another_game_not_found(
        self, authenticated_client, reported, game_factory
    ):
        other_game = game_factory()

        response = authenticated_client.post(
            self._url(reported, game=other_game),
            {"reason": ReportReason.MULTIPLE_ACCOUNTS, "note": "Same IP"},
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_game_master_can_report(
        self, authenticated_client, game, member_factory, primary_user
    ):
        member_factory(
            game=game, user=primary_user, nation=None, kind=MemberKind.GAME_MASTER
        )
        reported = member_factory(game=game)

        response = self._report(authenticated_client, reported)

        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_game_master_can_be_reported(
        self, authenticated_client, game, reporter, member_factory
    ):
        game_master = member_factory(game=game, kind=MemberKind.GAME_MASTER)

        response = self._report(authenticated_client, game_master)

        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    @pytest.mark.parametrize("departure", ["eliminated", "removed", "replaced"])
    def test_departed_member_can_be_reported(
        self, authenticated_client, game, reporter, member_factory, departure
    ):
        departed = member_factory(
            game=game, **self._departure(departure, game, member_factory)
        )

        response = self._report(authenticated_client, departed)

        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    @pytest.mark.parametrize("departure", ["eliminated", "removed", "replaced"])
    def test_departed_member_can_report(
        self,
        authenticated_client,
        game,
        member_factory,
        primary_user,
        departure,
    ):
        member_factory(
            game=game,
            user=primary_user,
            **self._departure(departure, game, member_factory),
        )
        reported = member_factory(game=game)

        response = self._report(authenticated_client, reported)

        assert response.status_code == status.HTTP_201_CREATED

    def _departure(self, departure, game, member_factory):
        if departure == "eliminated":
            return {"eliminated_at": timezone.now()}
        if departure == "removed":
            return {"removed_at": timezone.now()}
        return {"removed_at": timezone.now(), "replaced_by": member_factory(game=game)}

    @pytest.mark.django_db
    def test_member_without_user_refused(self, authenticated_client, reported):
        reported.user = None
        reported.save(update_fields=["user"])

        response = self._report(authenticated_client, reported)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "user_deleted"

    @pytest.mark.django_db
    @pytest.mark.parametrize("reason", [r["key"] for r in ReportReason.REASONS])
    def test_note_required(self, authenticated_client, reported, reason):
        response = self._report(
            authenticated_client, reported, reason=reason, note="  "
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "note" in response.data
        assert Report.objects.count() == 0

    @pytest.mark.django_db
    def test_note_over_limit_rejected(self, authenticated_client, reported):
        response = self._report(authenticated_client, reported, note="x" * 1001)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "note" in response.data

    @pytest.mark.django_db
    def test_unknown_reason_rejected(self, authenticated_client, reported):
        response = self._report(authenticated_client, reported, reason="lying")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "reason" in response.data


class TestMemberRetrieveReportFlags:
    def _retrieve(self, client, member):
        return client.get(
            reverse("game-member-retrieve", args=[member.game_id, member.id])
        )

    @pytest.mark.django_db
    def test_can_report_another_member(
        self, authenticated_client, game_factory, member_factory, primary_user
    ):
        game = game_factory()
        member_factory(game=game, user=primary_user)
        reported = member_factory(game=game)

        response = self._retrieve(authenticated_client, reported)

        assert response.data["can_report"] is True
        assert response.data["already_reported"] is False

    @pytest.mark.django_db
    def test_already_reported(
        self, authenticated_client, game_factory, member_factory, primary_user
    ):
        game = game_factory()
        member_factory(game=game, user=primary_user)
        reported = member_factory(game=game)
        Report.objects.report(reported, primary_user, ReportReason.OTHER, "Rude")

        response = self._retrieve(authenticated_client, reported)

        assert response.data["can_report"] is False
        assert response.data["already_reported"] is True

    @pytest.mark.django_db
    def test_cannot_report_own_member(
        self, authenticated_client, game_factory, member_factory, primary_user
    ):
        game = game_factory()
        own = member_factory(game=game, user=primary_user)

        response = self._retrieve(authenticated_client, own)

        assert response.data["can_report"] is False
        assert response.data["already_reported"] is False

    @pytest.mark.django_db
    def test_cannot_report_in_sandbox_game(
        self, authenticated_client, game_factory, member_factory, primary_user
    ):
        game = game_factory(sandbox=True)
        member_factory(game=game, user=primary_user)
        reported = member_factory(game=game)

        response = self._retrieve(authenticated_client, reported)

        assert response.data["can_report"] is False
        assert response.data["already_reported"] is False


class TestModeratorPolicy:
    @pytest.mark.django_db
    def test_allows_moderator(self, moderator):
        assert ModeratorPolicy.decide(None, moderator)

    @pytest.mark.django_db
    def test_refuses_user_without_flag(self, user_factory):
        decision = ModeratorPolicy.decide(None, user_factory(username="player"))

        assert not decision
        assert decision.reason == "not_moderator"

    @pytest.mark.django_db
    def test_refuses_staff_and_superuser_without_flag(self, user_factory):
        user = user_factory(username="staff")
        user.is_staff = True
        user.is_superuser = True
        user.save()

        assert not ModeratorPolicy.decide(None, user)

    @pytest.mark.django_db
    def test_refuses_system(self):
        assert not ModeratorPolicy.decide(None, SYSTEM)


class TestReportVisibility:
    @pytest.mark.django_db
    def test_moderator_sees_every_report(self, moderator, report_factory):
        reports = [report_factory(), report_factory()]

        assert set(Report.objects.visible_to(moderator)) == set(reports)

    @pytest.mark.django_db
    def test_reporter_sees_only_own_reports(self, report_factory):
        own = report_factory()
        report_factory()

        assert list(Report.objects.visible_to(own.reporter.user)) == [own]

    @pytest.mark.django_db
    def test_staff_superuser_without_flag_sees_no_reports(
        self, user_factory, report_factory
    ):
        report_factory()
        user = user_factory(username="staff")
        user.is_staff = True
        user.is_superuser = True
        user.save()

        assert not Report.objects.visible_to(user).exists()

    @pytest.mark.django_db
    def test_reported_player_sees_nothing(self, report_factory):
        report = report_factory()

        assert not Report.objects.visible_to(report.reported.user).exists()


class TestModerationReportListView:
    @pytest.mark.django_db
    def test_unauthenticated(self, unauthenticated_client):
        response = unauthenticated_client.get(LIST_URL, {"status": "pending"})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_non_moderator_not_found(self, authenticated_client, report_factory):
        report_factory()

        response = authenticated_client.get(LIST_URL, {"status": "pending"})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_non_moderator_not_found_without_status(self, authenticated_client):
        response = authenticated_client.get(LIST_URL)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_staff_superuser_without_flag_not_found(
        self, user_factory, authenticated_client_factory, report_factory
    ):
        report_factory()
        user = user_factory(username="staff")
        user.is_staff = True
        user.is_superuser = True
        user.save()

        response = authenticated_client_factory(user).get(
            LIST_URL, {"status": "pending"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_reporter_without_flag_not_found(
        self, authenticated_client_factory, report_factory
    ):
        report = report_factory()

        response = authenticated_client_factory(report.reporter.user).get(
            LIST_URL, {"status": "pending"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_status_required(self, moderator_client):
        response = moderator_client.get(LIST_URL)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_unknown_status_rejected(self, moderator_client):
        response = moderator_client.get(LIST_URL, {"status": "under_review"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_empty_queue(self, moderator_client):
        response = moderator_client.get(LIST_URL, {"status": "pending"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    @pytest.mark.django_db
    def test_pending_oldest_first(self, moderator_client, report_factory):
        newest = report_factory(age=timedelta(hours=1))
        oldest = report_factory(age=timedelta(days=3))
        middle = report_factory(age=timedelta(days=1))
        report_factory(decision=ReportDecision.APPROVED)
        report_factory(decision=ReportDecision.REJECTED)

        response = moderator_client.get(LIST_URL, {"status": "pending"})

        assert response.status_code == status.HTTP_200_OK
        assert [row["id"] for row in response.data] == [
            oldest.id,
            middle.id,
            newest.id,
        ]
        assert {row["status"] for row in response.data} == {"pending"}

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "decision", [ReportDecision.APPROVED, ReportDecision.REJECTED]
    )
    def test_decided_newest_first(self, moderator_client, report_factory, decision):
        older = report_factory(age=timedelta(days=2), decision=decision)
        newer = report_factory(age=timedelta(hours=2), decision=decision)
        report_factory()

        response = moderator_client.get(LIST_URL, {"status": decision})

        assert response.status_code == status.HTTP_200_OK
        assert [row["id"] for row in response.data] == [newer.id, older.id]
        assert {row["status"] for row in response.data} == {decision}

    @pytest.mark.django_db
    def test_row_shape(self, moderator_client, report_factory):
        report = report_factory(reason=ReportReason.SECRET_TEAMING)
        game = report.reporter.game

        response = moderator_client.get(LIST_URL, {"status": "pending"})

        assert response.data == [
            {
                "id": report.id,
                "reason": "secret_teaming",
                "note": "Insults in press.",
                "status": "pending",
                "created_at": response.data[0]["created_at"],
                "game_id": game.id,
                "game_name": game.name,
                "variant_name": game.variant.name,
                "reporter": {
                    "id": report.reporter.id,
                    "user_id": report.reporter.user_id,
                    "name": report.reporter.user.profile.name,
                    "nation": report.reporter.nation.name,
                },
                "reported": {
                    "id": report.reported.id,
                    "user_id": report.reported.user_id,
                    "name": report.reported.user.profile.name,
                    "nation": report.reported.nation.name,
                },
                "review": None,
                "assigned_to": None,
                "actions": [
                    {"key": "assign", "blocked_reason": None},
                    {"key": "unassign", "blocked_reason": "not_assignee"},
                    {"key": "approve", "blocked_reason": "not_assignee"},
                    {"key": "reject", "blocked_reason": "not_assignee"},
                ],
                "can_view_game": False,
            }
        ]

    @pytest.mark.django_db
    def test_anonymous_game_shows_real_identities(
        self, moderator_client, game_factory, report_factory
    ):
        report = report_factory(game=game_factory(anonymous=True))

        response = moderator_client.get(LIST_URL, {"status": "pending"})

        row = response.data[0]
        assert row["reporter"]["name"] == report.reporter.user.profile.name
        assert row["reporter"]["user_id"] == report.reporter.user_id
        assert row["reported"]["name"] == report.reported.user.profile.name
        assert row["reported"]["nation"] == report.reported.nation.name

    @pytest.mark.django_db
    def test_game_master_has_no_nation(
        self, moderator_client, game_factory, member_factory
    ):
        game = game_factory()
        game_master = member_factory(game=game)
        game_master.nation = None
        game_master.save()
        Report.objects.create(
            reporter=game_master,
            reported=member_factory(game=game),
            reason=ReportReason.OTHER,
            note="Spam",
        )

        response = moderator_client.get(LIST_URL, {"status": "pending"})

        assert response.data[0]["reporter"]["nation"] is None

    @pytest.mark.django_db
    def test_no_email_addresses(self, moderator_client, report_factory, moderator):
        report = report_factory(decision=ReportDecision.APPROVED, reviewed_by=moderator)

        response = moderator_client.get(LIST_URL, {"status": "approved"})

        body = response.content.decode()
        assert report.reporter.user.email not in body
        assert report.reported.user.email not in body
        assert moderator.email not in body
        assert "@" not in body

    @pytest.mark.django_db
    def test_query_count_does_not_grow(
        self, moderator_client, moderator, report_factory, django_assert_max_num_queries
    ):
        for _ in range(5):
            report_factory(decision=ReportDecision.APPROVED, reviewed_by=moderator)

        with django_assert_max_num_queries(3):
            response = moderator_client.get(LIST_URL, {"status": "approved"})

        assert len(response.data) == 5

    @pytest.mark.django_db
    def test_removing_flag_takes_effect_on_next_request(
        self, moderator, report_factory
    ):
        report_factory()
        client = _jwt_client(moderator)
        assert (
            client.get(LIST_URL, {"status": "pending"}).status_code
            == status.HTTP_200_OK
        )

        moderator.profile.is_moderator = False
        moderator.profile.save()

        response = client.get(LIST_URL, {"status": "pending"})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_granting_flag_takes_effect_on_next_request(self, user_factory):
        user = user_factory(username="player")
        client = _jwt_client(user)
        assert (
            client.get(LIST_URL, {"status": "pending"}).status_code
            == status.HTTP_404_NOT_FOUND
        )

        user.profile.is_moderator = True
        user.profile.save()

        response = client.get(LIST_URL, {"status": "pending"})

        assert response.status_code == status.HTTP_200_OK


class TestModerationReportDetailView:
    @pytest.mark.django_db
    def test_unauthenticated(self, unauthenticated_client, report_factory):
        response = unauthenticated_client.get(_detail_url(report_factory()))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_moderator_sees_report(self, moderator_client, report_factory):
        report = report_factory(reason=ReportReason.MULTIPLE_ACCOUNTS)

        response = moderator_client.get(_detail_url(report))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == report.id
        assert response.data["reason"] == "multiple_accounts"
        assert response.data["note"] == "Insults in press."
        assert response.data["reporter"]["name"] == report.reporter.user.profile.name
        assert response.data["reported"]["name"] == report.reported.user.profile.name
        assert response.data["game_name"] == report.reporter.game.name

    @pytest.mark.django_db
    def test_decided_report_shows_review(
        self, moderator_client, moderator, report_factory
    ):
        report = report_factory(
            decision=ReportDecision.REJECTED,
            reviewed_by=moderator,
            review_note="Ordinary diplomacy, not a breach.",
        )

        response = moderator_client.get(_detail_url(report))

        assert response.data["status"] == "rejected"
        assert response.data["review"] == {
            "reviewed_by": {"user_id": moderator.id, "name": "Mia Moderator"},
            "note": "Ordinary diplomacy, not a breach.",
            "created_at": response.data["review"]["created_at"],
        }

    @pytest.mark.django_db
    def test_review_note_defaults_to_empty(self, moderator, report_factory):
        report = report_factory()
        review = ReportReview.objects.create(
            report=report, decision=ReportDecision.APPROVED, reviewed_by=moderator
        )
        review.refresh_from_db()

        assert review.note == ""

    @pytest.mark.django_db
    def test_missing_report_not_found(self, moderator_client):
        response = moderator_client.get(
            reverse("moderation-report-detail", args=[999999])
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_reporter_without_flag_not_found(
        self, authenticated_client_factory, report_factory
    ):
        report = report_factory()

        response = authenticated_client_factory(report.reporter.user).get(
            _detail_url(report)
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_staff_superuser_without_flag_not_found(
        self, user_factory, authenticated_client_factory, report_factory
    ):
        user = user_factory(username="staff")
        user.is_staff = True
        user.is_superuser = True
        user.save()

        response = authenticated_client_factory(user).get(_detail_url(report_factory()))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_removing_flag_takes_effect_on_next_request(
        self, moderator, report_factory
    ):
        report = report_factory()
        client = _jwt_client(moderator)
        assert client.get(_detail_url(report)).status_code == status.HTTP_200_OK

        moderator.profile.is_moderator = False
        moderator.profile.save()

        response = client.get(_detail_url(report))

        assert response.status_code == status.HTTP_404_NOT_FOUND


def _assign_url(report):
    return reverse("moderation-report-assign", args=[report.id])


def _unassign_url(report):
    return reverse("moderation-report-unassign", args=[report.id])


def _blocked_reasons(data):
    return {action["key"]: action["blocked_reason"] for action in data["actions"]}


class TestModerationReportAssignView:
    @pytest.mark.django_db
    def test_unauthenticated(self, unauthenticated_client, report_factory):
        response = unauthenticated_client.post(_assign_url(report_factory()))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_non_moderator_not_found(self, authenticated_client, report_factory):
        report = report_factory()

        response = authenticated_client.post(_assign_url(report))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        report.refresh_from_db()
        assert report.assigned_to is None

    @pytest.mark.django_db
    def test_missing_report_not_found(self, moderator_client):
        response = moderator_client.post(
            reverse("moderation-report-assign", args=[999999])
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_moderator_takes_unassigned_report(
        self, moderator_client, moderator, report_factory
    ):
        report = report_factory()

        response = moderator_client.post(_assign_url(report))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == report.id
        assert response.data["assigned_to"] == {
            "user_id": moderator.id,
            "name": "Mia Moderator",
        }
        assert _blocked_reasons(response.data) == {
            "assign": "already_assigned",
            "unassign": None,
            "approve": None,
            "reject": None,
        }
        report.refresh_from_db()
        assert report.assigned_to == moderator

    @pytest.mark.django_db
    def test_report_taken_by_another_moderator_refused(
        self, moderator_client, user_factory, report_factory
    ):
        other = user_factory(username="other", name="Sam Moderator")
        report = report_factory()
        Report.objects.filter(pk=report.pk).update(assigned_to=other)

        response = moderator_client.post(_assign_url(report))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "already_assigned"
        report.refresh_from_db()
        assert report.assigned_to == other

    @pytest.mark.django_db
    def test_report_already_taken_by_self_refused(
        self, moderator_client, moderator, report_factory
    ):
        report = report_factory()
        Report.objects.filter(pk=report.pk).update(assigned_to=moderator)

        response = moderator_client.post(_assign_url(report))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "already_assigned"

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "decision", [ReportDecision.APPROVED, ReportDecision.REJECTED]
    )
    def test_reviewed_report_refused(
        self, moderator_client, moderator, report_factory, decision
    ):
        report = report_factory(decision=decision, reviewed_by=moderator)

        response = moderator_client.post(_assign_url(report))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "already_reviewed"

    @pytest.mark.django_db
    def test_moderator_in_game_refused(
        self, moderator_client, moderator, game_factory, member_factory, report_factory
    ):
        game = game_factory()
        member_factory(game=game, user=moderator)
        report = report_factory(game=game)

        response = moderator_client.post(_assign_url(report))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "game_member"
        report.refresh_from_db()
        assert report.assigned_to is None

    @pytest.mark.django_db
    def test_game_master_moderator_refused(
        self, moderator_client, moderator, game_factory, member_factory, report_factory
    ):
        game = game_factory()
        game_master = member_factory(game=game, user=moderator)
        game_master.nation = None
        game_master.save()
        report = report_factory(game=game)

        response = moderator_client.post(_assign_url(report))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "game_member"

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "departure",
        [{"eliminated_at": timezone.now()}, {"removed_at": timezone.now()}],
    )
    def test_moderator_who_left_game_refused(
        self,
        moderator_client,
        moderator,
        game_factory,
        member_factory,
        report_factory,
        departure,
    ):
        game = game_factory()
        member_factory(game=game, user=moderator, **departure)
        report = report_factory(game=game)

        response = moderator_client.post(_assign_url(report))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "game_member"

    @pytest.mark.django_db
    def test_membership_of_another_game_allowed(
        self, moderator_client, moderator, member_factory, report_factory
    ):
        member_factory(user=moderator)
        report = report_factory()

        response = moderator_client.post(_assign_url(report))

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.django_db
    def test_get_not_allowed(self, moderator_client, report_factory):
        response = moderator_client.get(_assign_url(report_factory()))

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestModerationReportUnassignView:
    @pytest.mark.django_db
    def test_unauthenticated(self, unauthenticated_client, report_factory):
        response = unauthenticated_client.post(_unassign_url(report_factory()))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    def test_non_moderator_not_found(self, authenticated_client, report_factory):
        response = authenticated_client.post(_unassign_url(report_factory()))

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_assignee_unassigns(self, moderator_client, moderator, report_factory):
        report = report_factory()
        Report.objects.filter(pk=report.pk).update(assigned_to=moderator)

        response = moderator_client.post(_unassign_url(report))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["assigned_to"] is None
        assert _blocked_reasons(response.data) == {
            "assign": None,
            "unassign": "not_assignee",
            "approve": "not_assignee",
            "reject": "not_assignee",
        }
        report.refresh_from_db()
        assert report.assigned_to is None

    @pytest.mark.django_db
    def test_unassigned_report_can_be_taken_by_another_moderator(
        self,
        moderator_client,
        moderator,
        user_factory,
        authenticated_client_factory,
        report_factory,
    ):
        report = report_factory()
        moderator_client.post(_assign_url(report))
        moderator_client.post(_unassign_url(report))
        other = user_factory(username="other", name="Sam Moderator")
        other.profile.is_moderator = True
        other.profile.save()

        response = authenticated_client_factory(other).post(_assign_url(report))

        assert response.status_code == status.HTTP_200_OK
        report.refresh_from_db()
        assert report.assigned_to == other

    @pytest.mark.django_db
    def test_another_moderators_report_refused(
        self, moderator_client, user_factory, report_factory
    ):
        other = user_factory(username="other", name="Sam Moderator")
        report = report_factory()
        Report.objects.filter(pk=report.pk).update(assigned_to=other)

        response = moderator_client.post(_unassign_url(report))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "not_assignee"
        report.refresh_from_db()
        assert report.assigned_to == other

    @pytest.mark.django_db
    def test_unassigned_report_refused(self, moderator_client, report_factory):
        response = moderator_client.post(_unassign_url(report_factory()))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "not_assignee"

    @pytest.mark.django_db
    def test_reviewed_report_refused(self, moderator_client, moderator, report_factory):
        report = report_factory(decision=ReportDecision.APPROVED, reviewed_by=moderator)
        Report.objects.filter(pk=report.pk).update(assigned_to=moderator)

        response = moderator_client.post(_unassign_url(report))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "already_reviewed"


def _approve_url(report):
    return reverse("moderation-report-approve", args=[report.id])


def _reject_url(report):
    return reverse("moderation-report-reject", args=[report.id])


@pytest.fixture
def assigned_report(report_factory, moderator):
    report = report_factory()
    Report.objects.filter(pk=report.pk).update(assigned_to=moderator)
    report.refresh_from_db()
    return report


@pytest.fixture
def second_report_factory(db, member_factory, moderator):
    def _create(report, reason=None):
        second = Report.objects.create(
            reporter=member_factory(game=report.game),
            reported=report.reported,
            reason=reason or report.reason,
            note="Same again.",
            assigned_to=moderator,
        )
        return second

    return _create


class TestModerationReportDecisionViews:
    @pytest.mark.django_db
    @pytest.mark.parametrize("url", [_approve_url, _reject_url])
    def test_unauthenticated(self, unauthenticated_client, assigned_report, url):
        response = unauthenticated_client.post(url(assigned_report))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.django_db
    @pytest.mark.parametrize("url", [_approve_url, _reject_url])
    def test_non_moderator_not_found(self, authenticated_client, assigned_report, url):
        response = authenticated_client.post(url(assigned_report))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert not ReportReview.objects.filter(report=assigned_report).exists()

    @pytest.mark.django_db
    def test_missing_report_not_found(self, moderator_client):
        response = moderator_client.post(
            reverse("moderation-report-approve", args=[999999])
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_assignee_approves(self, moderator_client, moderator, assigned_report):
        response = moderator_client.post(
            _approve_url(assigned_report),
            {"note": "Slurs in global press."},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "approved"
        assert response.data["review"] == {
            "reviewed_by": {"user_id": moderator.id, "name": "Mia Moderator"},
            "note": "Slurs in global press.",
            "created_at": response.data["review"]["created_at"],
        }
        assert _blocked_reasons(response.data) == {
            "assign": "already_reviewed",
            "unassign": "already_reviewed",
            "approve": "already_reviewed",
            "reject": "already_reviewed",
        }
        assert list(Mark.objects.values_list("member_id", "reason")) == [
            (assigned_report.reported_id, ReportReason.ABUSE_AND_HARASSMENT)
        ]

    @pytest.mark.django_db
    def test_assignee_rejects(self, moderator_client, moderator, assigned_report):
        response = moderator_client.post(
            _reject_url(assigned_report), {"note": "Ordinary diplomacy."}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "rejected"
        assert response.data["review"]["reviewed_by"] == {
            "user_id": moderator.id,
            "name": "Mia Moderator",
        }
        assert response.data["review"]["note"] == "Ordinary diplomacy."
        assert not Mark.objects.exists()

    @pytest.mark.django_db
    @pytest.mark.parametrize("url", [_approve_url, _reject_url])
    def test_note_optional(self, moderator_client, assigned_report, url):
        response = moderator_client.post(url(assigned_report))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["review"]["note"] == ""

    @pytest.mark.django_db
    def test_note_over_limit_rejected(self, moderator_client, assigned_report):
        response = moderator_client.post(
            _approve_url(assigned_report), {"note": "x" * 1001}, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not ReportReview.objects.filter(report=assigned_report).exists()
        assert not Mark.objects.exists()

    @pytest.mark.django_db
    @pytest.mark.parametrize("url", [_approve_url, _reject_url])
    def test_unassigned_report_refused(self, moderator_client, report_factory, url):
        report = report_factory()

        response = moderator_client.post(url(report))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "not_assignee"
        assert not ReportReview.objects.filter(report=report).exists()

    @pytest.mark.django_db
    @pytest.mark.parametrize("url", [_approve_url, _reject_url])
    def test_another_moderators_report_refused(
        self, other_moderator_client, assigned_report, url
    ):
        response = other_moderator_client.post(url(assigned_report))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "not_assignee"
        assert not ReportReview.objects.filter(report=assigned_report).exists()

    @pytest.mark.django_db
    @pytest.mark.parametrize("url", [_approve_url, _reject_url])
    def test_former_moderator_refused(
        self, moderator_client, moderator, assigned_report, url
    ):
        moderator.profile.is_moderator = False
        moderator.profile.save()

        response = moderator_client.post(url(assigned_report))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert not ReportReview.objects.filter(report=assigned_report).exists()

    @pytest.mark.django_db
    @pytest.mark.parametrize("url", [_approve_url, _reject_url])
    def test_assignee_who_joined_game_refused(
        self, moderator_client, moderator, member_factory, assigned_report, url
    ):
        member_factory(game=assigned_report.game, user=moderator)

        response = moderator_client.post(url(assigned_report))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "game_member"
        assert not ReportReview.objects.filter(report=assigned_report).exists()

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "decision", [ReportDecision.APPROVED, ReportDecision.REJECTED]
    )
    @pytest.mark.parametrize("url", [_approve_url, _reject_url])
    def test_decided_report_refused(
        self, moderator_client, moderator, report_factory, decision, url
    ):
        report = report_factory(
            decision=decision, reviewed_by=moderator, review_note="First call."
        )
        Report.objects.filter(pk=report.pk).update(assigned_to=moderator)

        response = moderator_client.post(
            url(report), {"note": "Second call."}, format="json"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "already_reviewed"
        report.review.refresh_from_db()
        assert report.review.decision == decision
        assert report.review.note == "First call."
        assert not Mark.objects.exists()

    @pytest.mark.django_db
    def test_approving_same_reason_twice_gives_one_mark(
        self, moderator_client, assigned_report, second_report_factory
    ):
        second = second_report_factory(assigned_report)

        moderator_client.post(_approve_url(assigned_report))
        response = moderator_client.post(_approve_url(second))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["status"] == "approved"
        assert list(Mark.objects.values_list("member_id", "reason")) == [
            (assigned_report.reported_id, ReportReason.ABUSE_AND_HARASSMENT)
        ]

    @pytest.mark.django_db
    def test_approving_different_reasons_gives_one_mark_each(
        self, moderator_client, assigned_report, second_report_factory
    ):
        second = second_report_factory(
            assigned_report, reason=ReportReason.SECRET_TEAMING
        )

        moderator_client.post(_approve_url(assigned_report))
        moderator_client.post(_approve_url(second))

        assert set(Mark.objects.values_list("member_id", "reason")) == {
            (assigned_report.reported_id, ReportReason.ABUSE_AND_HARASSMENT),
            (assigned_report.reported_id, ReportReason.SECRET_TEAMING),
        }

    @pytest.mark.django_db
    def test_rejecting_after_approval_leaves_mark(
        self, moderator_client, assigned_report, second_report_factory
    ):
        second = second_report_factory(assigned_report)

        moderator_client.post(_approve_url(assigned_report))
        moderator_client.post(_reject_url(second))

        assert Mark.objects.count() == 1

    @pytest.mark.django_db
    def test_same_reason_in_another_game_gives_another_mark(
        self, moderator_client, moderator, report_factory, assigned_report
    ):
        other = report_factory()
        Member.objects.filter(pk=other.reported_id).update(
            user=assigned_report.reported.user
        )
        Report.objects.filter(pk=other.pk).update(assigned_to=moderator)

        moderator_client.post(_approve_url(assigned_report))
        moderator_client.post(_approve_url(other))

        assert set(Mark.objects.values_list("member_id", flat=True)) == {
            assigned_report.reported_id,
            other.reported_id,
        }

    @pytest.mark.django_db
    def test_approved_report_in_approved_queue(
        self, moderator_client, moderator, assigned_report
    ):
        moderator_client.post(
            _approve_url(assigned_report), {"note": "Clear."}, format="json"
        )

        pending = moderator_client.get(LIST_URL, {"status": "pending"})
        approved = moderator_client.get(LIST_URL, {"status": "approved"})

        assert pending.data == []
        assert [row["id"] for row in approved.data] == [assigned_report.id]
        assert approved.data[0]["review"]["reviewed_by"] == {
            "user_id": moderator.id,
            "name": "Mia Moderator",
        }
        assert approved.data[0]["review"]["created_at"] is not None

    @pytest.mark.django_db
    def test_rejected_report_in_rejected_queue(self, moderator_client, assigned_report):
        moderator_client.post(_reject_url(assigned_report))

        rejected = moderator_client.get(LIST_URL, {"status": "rejected"})

        assert [row["id"] for row in rejected.data] == [assigned_report.id]

    @pytest.mark.django_db
    @pytest.mark.parametrize("url", [_approve_url, _reject_url])
    def test_get_not_allowed(self, moderator_client, assigned_report, url):
        response = moderator_client.get(url(assigned_report))

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


class TestMarkManager:
    @pytest.mark.django_db
    def test_create_idempotent_creates_mark(self, report_factory):
        report = report_factory()

        mark = Mark.objects.create_idempotent(
            member=report.reported, reason=report.reason
        )

        assert mark.member == report.reported
        assert mark.reason == report.reason

    @pytest.mark.django_db
    def test_create_idempotent_returns_existing_mark(self, report_factory):
        report = report_factory()
        existing = Mark.objects.create(member=report.reported, reason=report.reason)

        mark = Mark.objects.create_idempotent(
            member=report.reported, reason=report.reason
        )

        assert mark == existing
        assert Mark.objects.count() == 1


class TestModerationQueueAssignment:
    @pytest.mark.django_db
    def test_shows_who_has_each_report(
        self, moderator_client, user_factory, report_factory
    ):
        other = user_factory(username="other", name="Sam Moderator")
        taken = report_factory(age=timedelta(days=1))
        free = report_factory()
        Report.objects.filter(pk=taken.pk).update(assigned_to=other)

        response = moderator_client.get(LIST_URL, {"status": "pending"})

        rows = {row["id"]: row for row in response.data}
        assert rows[taken.id]["assigned_to"] == {
            "user_id": other.id,
            "name": "Sam Moderator",
        }
        assert _blocked_reasons(rows[taken.id]) == {
            "assign": "already_assigned",
            "unassign": "not_assignee",
            "approve": "not_assignee",
            "reject": "not_assignee",
        }
        assert rows[free.id]["assigned_to"] is None
        assert _blocked_reasons(rows[free.id])["assign"] is None

    @pytest.mark.django_db
    def test_lists_reports_from_own_game_with_reason(
        self, moderator_client, moderator, game_factory, member_factory, report_factory
    ):
        game = game_factory()
        member_factory(game=game, user=moderator)
        report = report_factory(game=game)

        response = moderator_client.get(LIST_URL, {"status": "pending"})

        assert [row["id"] for row in response.data] == [report.id]
        assert _blocked_reasons(response.data[0])["assign"] == "game_member"

    @pytest.mark.django_db
    def test_query_count_does_not_grow(
        self,
        moderator_client,
        moderator,
        user_factory,
        report_factory,
        django_assert_max_num_queries,
    ):
        other = user_factory(username="other", name="Sam Moderator")
        for _ in range(5):
            report = report_factory()
            Report.objects.filter(pk=report.pk).update(assigned_to=other)

        with django_assert_max_num_queries(4):
            response = moderator_client.get(LIST_URL, {"status": "pending"})

        assert len(response.data) == 5


@pytest.fixture
def moderated_game(
    game_factory,
    phase_factory,
    member_factory,
    report_factory,
    moderator,
    classical_variant,
    classical_london_province,
):
    game = game_factory(variant=classical_variant, anonymous=True)
    phase = phase_factory(game=game)
    report = report_factory(game=game)
    Report.objects.filter(pk=report.pk).update(assigned_to=moderator)
    bystander = member_factory(game=game)
    private_channel = Channel.objects.create(
        game=game, name="Private Channel", private=True
    )
    private_channel.members.set([report.reporter, report.reported])
    ChannelMessage.objects.create(
        channel=private_channel, sender=report.reported, body="Secret plan"
    )
    public_channel = Channel.objects.create(
        game=game, name="Public Press", private=False
    )
    phase_state = phase.phase_states.create(member=report.reported)
    Order.objects.create(
        phase_state=phase_state,
        order_type=OrderType.HOLD,
        source=classical_london_province,
    )
    report.refresh_from_db()
    report.bystander = bystander
    report.private_channel = private_channel
    report.public_channel = public_channel
    report.phase = phase
    return report


@pytest.fixture
def other_moderator_client(user_factory, authenticated_client_factory):
    other = user_factory(username="other", name="Sam Moderator")
    other.profile.is_moderator = True
    other.profile.save()
    return authenticated_client_factory(other)


def _channel_ids(client, report):
    response = client.get(reverse("channel-preview-list", args=[report.game.id]))
    return {channel["id"] for channel in response.data}


def _member_names(client, game):
    response = client.get(reverse("game-retrieve", args=[game.id]))
    return sorted(member["name"] for member in response.data["members"])


def _messages_url(channel):
    return reverse("channel-message-list", args=[channel.game_id, channel.id])


class TestCanModerateGamePolicy:
    @pytest.mark.django_db
    def test_assignee_of_pending_report_allowed(self, moderated_game, moderator):
        assert CanModerateGamePolicy.decide(moderated_game.game, moderator)

    @pytest.mark.django_db
    def test_moderator_without_report_in_game_refused(
        self, moderated_game, user_factory
    ):
        other = user_factory(username="other", name="Sam Moderator")
        other.profile.is_moderator = True
        other.profile.save()

        decision = CanModerateGamePolicy.decide(moderated_game.game, other)

        assert decision.reason == "not_assignee"

    @pytest.mark.django_db
    def test_unassigned_report_refused(self, moderated_game, moderator):
        moderated_game.unassign()

        decision = CanModerateGamePolicy.decide(moderated_game.game, moderator)

        assert decision.reason == "not_assignee"

    @pytest.mark.django_db
    def test_reviewed_report_refused(self, moderated_game, moderator):
        ReportReview.objects.create(
            report=moderated_game,
            decision=ReportDecision.REJECTED,
            reviewed_by=moderator,
        )

        decision = CanModerateGamePolicy.decide(moderated_game.game, moderator)

        assert decision.reason == "not_assignee"

    @pytest.mark.django_db
    def test_moderator_who_joined_game_refused(
        self, moderated_game, moderator, member_factory
    ):
        member_factory(game=moderated_game.game, user=moderator)

        decision = CanModerateGamePolicy.decide(moderated_game.game, moderator)

        assert decision.reason == "game_member"

    @pytest.mark.django_db
    def test_former_moderator_refused(self, moderated_game, moderator):
        moderator.profile.is_moderator = False
        moderator.profile.save()

        decision = CanModerateGamePolicy.decide(moderated_game.game, moderator)

        assert decision.reason == "not_moderator"

    @pytest.mark.django_db
    def test_unassigned_report_does_not_match_anonymous_user(self, report_factory):
        report = report_factory()

        assert not IsAssignedInGameCheck.decide(report.game, AnonymousUser())


class TestModerationReportCanViewGame:
    @pytest.mark.django_db
    def test_assignee_can_view_game(self, moderator_client, moderated_game):
        response = moderator_client.get(_detail_url(moderated_game))

        assert response.data["can_view_game"] is True

    @pytest.mark.django_db
    def test_unassigned_report_cannot_view_game(self, moderator_client, report_factory):
        response = moderator_client.get(_detail_url(report_factory()))

        assert response.data["can_view_game"] is False

    @pytest.mark.django_db
    def test_another_moderators_report_cannot_view_game(
        self, other_moderator_client, moderated_game
    ):
        response = other_moderator_client.get(_detail_url(moderated_game))

        assert response.data["can_view_game"] is False

    @pytest.mark.django_db
    def test_reviewed_report_cannot_view_game(
        self, moderator_client, moderator, moderated_game
    ):
        ReportReview.objects.create(
            report=moderated_game,
            decision=ReportDecision.APPROVED,
            reviewed_by=moderator,
        )

        response = moderator_client.get(_detail_url(moderated_game))

        assert response.data["can_view_game"] is False

    @pytest.mark.django_db
    def test_queue_query_count_does_not_grow(
        self,
        moderator_client,
        moderator,
        report_factory,
        django_assert_max_num_queries,
    ):
        for _ in range(5):
            report = report_factory()
            Report.objects.filter(pk=report.pk).update(assigned_to=moderator)

        with django_assert_max_num_queries(4):
            response = moderator_client.get(LIST_URL, {"status": "pending"})

        assert [row["can_view_game"] for row in response.data] == [True] * 5


class TestModeratorGameChannels:
    @pytest.mark.django_db
    def test_assignee_sees_private_channels(self, moderator_client, moderated_game):
        ids = _channel_ids(moderator_client, moderated_game)

        assert ids == {
            moderated_game.public_channel.id,
            moderated_game.private_channel.id,
        }

    @pytest.mark.django_db
    def test_other_moderator_sees_only_public_channels(
        self, other_moderator_client, moderated_game
    ):
        ids = _channel_ids(other_moderator_client, moderated_game)

        assert ids == {moderated_game.public_channel.id}

    @pytest.mark.django_db
    def test_access_ends_on_unassign(self, moderator_client, moderated_game):
        moderator_client.post(_unassign_url(moderated_game))

        ids = _channel_ids(moderator_client, moderated_game)

        assert ids == {moderated_game.public_channel.id}

    @pytest.mark.django_db
    def test_access_ends_on_decision(self, moderator_client, moderator, moderated_game):
        ReportReview.objects.create(
            report=moderated_game,
            decision=ReportDecision.APPROVED,
            reviewed_by=moderator,
        )

        ids = _channel_ids(moderator_client, moderated_game)

        assert ids == {moderated_game.public_channel.id}

    @pytest.mark.django_db
    def test_assignee_reads_private_messages(self, moderator_client, moderated_game):
        response = moderator_client.get(_messages_url(moderated_game.private_channel))

        assert response.status_code == status.HTTP_200_OK
        assert [message["body"] for message in response.data["results"]] == [
            "Secret plan"
        ]
        assert response.data["results"][0]["sender"]["user_id"] == (
            moderated_game.reported.user_id
        )

    @pytest.mark.django_db
    def test_other_moderator_cannot_read_private_messages(
        self, other_moderator_client, moderated_game
    ):
        response = other_moderator_client.get(
            _messages_url(moderated_game.private_channel)
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_assignee_retrieves_private_channel_read_only(
        self, moderator_client, moderated_game
    ):
        channel = moderated_game.private_channel

        response = moderator_client.get(
            reverse("channel-update", args=[channel.game_id, channel.id])
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["can_mute"] is False
        assert response.data["can_rename"] is False

    @pytest.mark.django_db
    def test_assignee_cannot_send_message(self, moderator_client, moderated_game):
        channel = moderated_game.private_channel

        response = moderator_client.post(
            reverse("channel-message-create", args=[channel.game_id, channel.id]),
            {"body": "Hello"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert channel.messages.count() == 1

    @pytest.mark.django_db
    def test_assignee_cannot_mark_channel_read(self, moderator_client, moderated_game):
        channel = moderated_game.private_channel

        response = moderator_client.post(
            reverse("channel-mark-read", args=[channel.game_id, channel.id])
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_assignee_cannot_create_channel(self, moderator_client, moderated_game):
        game = moderated_game.game

        response = moderator_client.post(
            reverse("channel-create", args=[game.id]),
            {"member_ids": [moderated_game.reported.id]},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert game.channels.count() == 2


class TestModeratorGameRetrieve:
    @pytest.mark.django_db
    def test_assignee_sees_real_identities(self, moderator_client, moderated_game):
        report = moderated_game

        names = _member_names(moderator_client, report.game)

        assert names == sorted(
            member.user.profile.name
            for member in (report.reporter, report.reported, report.bystander)
        )

    @pytest.mark.django_db
    def test_other_moderator_sees_anonymous_players(
        self, other_moderator_client, moderated_game
    ):
        names = _member_names(other_moderator_client, moderated_game.game)

        assert names == ["Anonymous"] * 3

    @pytest.mark.django_db
    def test_identities_hidden_again_after_unassign(
        self, moderator_client, moderated_game
    ):
        moderator_client.post(_unassign_url(moderated_game))

        names = _member_names(moderator_client, moderated_game.game)

        assert names == ["Anonymous"] * 3

    @pytest.mark.django_db
    def test_assignee_sees_real_identity_on_member(
        self, moderator_client, moderated_game
    ):
        reported = moderated_game.reported

        response = moderator_client.get(
            reverse("game-member-retrieve", args=[reported.game_id, reported.id])
        )

        assert response.data["name"] == reported.user.profile.name
        assert response.data["can_report"] is False

    @pytest.mark.django_db
    def test_players_see_no_sign_of_moderator(
        self, authenticated_client_factory, moderator_client, moderator, moderated_game
    ):
        game = moderated_game.game
        moderator_client.get(reverse("game-retrieve", args=[game.id]))
        moderator_client.get(_messages_url(moderated_game.private_channel))

        response = authenticated_client_factory(moderated_game.reported.user).get(
            reverse("game-retrieve", args=[game.id])
        )

        assert moderator.id not in {
            member["user_id"] for member in response.data["members"]
        }
        assert game.members.count() == 3

    @pytest.mark.django_db
    def test_etag_changes_when_assigned(
        self, authenticated_client_factory, moderator, report_factory, game_factory
    ):
        report = report_factory(game=game_factory(anonymous=True))
        client = authenticated_client_factory(moderator)
        url = reverse("game-retrieve", args=[report.game.id])
        etag = client.get(url)["ETag"]
        client.post(_assign_url(report))

        response = client.get(url, HTTP_IF_NONE_MATCH=etag)

        assert response.status_code == status.HTTP_200_OK
        assert response["ETag"] != etag

    @pytest.mark.django_db
    def test_etag_changes_when_decided(
        self, moderator_client, moderator, moderated_game
    ):
        url = reverse("game-retrieve", args=[moderated_game.game.id])
        etag = moderator_client.get(url)["ETag"]
        ReportReview.objects.create(
            report=moderated_game,
            decision=ReportDecision.REJECTED,
            reviewed_by=moderator,
        )

        response = moderator_client.get(url, HTTP_IF_NONE_MATCH=etag)

        assert response.status_code == status.HTTP_200_OK
        assert response["ETag"] != etag


class TestModeratorGameOrders:
    @pytest.mark.django_db
    def test_unresolved_orders_hidden(self, moderator_client, moderated_game):
        phase = moderated_game.phase

        response = moderator_client.get(
            reverse("order-list", args=[phase.game_id, phase.id])
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data == []

    @pytest.mark.django_db
    def test_assignee_cannot_create_order(self, moderator_client, moderated_game):
        game = moderated_game.game

        response = moderator_client.post(
            reverse("order-create", args=[game.id]),
            {"selected": ["lon", "Hold"]},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert (
            Order.objects.filter(phase_state__phase=moderated_game.phase).count() == 1
        )
