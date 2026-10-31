from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from common.actors import SYSTEM
from moderator.models import ModerationReport
from moderator.policies import ModeratorPolicy
from report.constants import ReportDecision, ReportReason
from report.models import Report, ReportReview

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
        Report.objects.filter(pk=report.pk).update(
            created_at=timezone.now() - age
        )
        if decision is not None:
            ReportReview.objects.create(
                report=report,
                decision=decision,
                reviewed_by=reviewed_by or reporter.user,
            )
        return report

    return _create


def _detail_url(report):
    return reverse("moderation-report-detail", args=[report.id])


def _jwt_client(user):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {AccessToken.for_user(user)}")
    return client


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


class TestModerationReportQuerySet:
    @pytest.mark.django_db
    def test_moderator_sees_every_report(self, moderator, report_factory):
        report = report_factory()

        assert list(ModerationReport.objects.visible_to(moderator)) == [report]

    @pytest.mark.django_db
    def test_reporter_without_flag_sees_nothing(self, report_factory):
        report = report_factory()

        assert not ModerationReport.objects.visible_to(report.reporter.user).exists()


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
        self, moderator_client, report_factory, django_assert_max_num_queries
    ):
        for _ in range(5):
            report_factory()

        with django_assert_max_num_queries(3):
            response = moderator_client.get(LIST_URL, {"status": "pending"})

        assert len(response.data) == 5

    @pytest.mark.django_db
    def test_removing_flag_takes_effect_on_next_request(
        self, moderator, report_factory
    ):
        report_factory()
        client = _jwt_client(moderator)
        assert client.get(LIST_URL, {"status": "pending"}).status_code == status.HTTP_200_OK

        moderator.profile.is_moderator = False
        moderator.profile.save()

        response = client.get(LIST_URL, {"status": "pending"})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.django_db
    def test_granting_flag_takes_effect_on_next_request(self, user_factory):
        user = user_factory(username="player")
        client = _jwt_client(user)
        assert client.get(LIST_URL, {"status": "pending"}).status_code == status.HTTP_404_NOT_FOUND

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
    def test_decided_report_status(self, moderator_client, report_factory):
        report = report_factory(decision=ReportDecision.REJECTED)

        response = moderator_client.get(_detail_url(report))

        assert response.data["status"] == "rejected"

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

        response = authenticated_client_factory(user).get(
            _detail_url(report_factory())
        )

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
