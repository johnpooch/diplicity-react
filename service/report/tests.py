from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from common.actors import SYSTEM
from common.constants import GameStatus, MemberKind
from common.policies import Refused
from report.constants import ReportDecision, ReportReason, ReportStatus
from report.models import Report, ReportReview
from report.policies import ModeratorPolicy

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
        Report.objects.filter(pk=report.pk).update(
            created_at=timezone.now() - age
        )
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
