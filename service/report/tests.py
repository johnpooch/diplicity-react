import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from common.constants import GameStatus, MemberKind
from common.policies import Refused
from report.constants import ReportDecision, ReportReason, ReportStatus
from report.models import Report, ReportReview


@pytest.fixture
def report_factory(db, game_factory, member_factory):
    def _create(decision=None, reviewed_by=None):
        game = game_factory()
        reporter = member_factory(game=game)
        reported = member_factory(game=game)
        report = Report.objects.create(
            game=game,
            reporter=reporter.user,
            reported_member=reported,
            reported_user=reported.user,
            reason=ReportReason.ABUSE_AND_HARASSMENT,
        )
        if decision is not None:
            ReportReview.objects.create(
                report=report,
                decision=decision,
                reviewed_by=reviewed_by or reporter.user,
            )
        return report

    return _create


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
    def test_report_records_the_user_behind_the_seat(
        self, game_factory, member_factory
    ):
        game = game_factory()
        reporter = member_factory(game=game)
        reported = member_factory(game=game)

        report = Report.objects.report(
            reported, reporter.user, ReportReason.SECRET_TEAMING, ""
        )

        assert report.game == game
        assert report.reporter == reporter.user
        assert report.reported_member == reported
        assert report.reported_user == reported.user

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

    def _report(self, client, member, reason=ReportReason.ABUSE_AND_HARASSMENT, **data):
        return client.post(self._url(member), {"reason": reason, **data}, format="json")

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
    def test_creates_report(self, authenticated_client, reported, primary_user):
        response = self._report(
            authenticated_client, reported, note="Called me names in press."
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["reason"] == "abuse_and_harassment"
        assert response.data["note"] == "Called me names in press."
        assert response.data["status"] == "pending"
        report = Report.objects.get()
        assert report.reporter == primary_user
        assert report.reported_member == reported
        assert report.reported_user == reported.user

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
            "reported_member",
            "reason",
            "note",
            "status",
            "created_at",
        }
        assert response.data["reported_member"] == reported.id

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
    def test_another_seat_held_by_the_same_user_is_a_duplicate(
        self, authenticated_client, game, reported, member_factory
    ):
        other_seat = member_factory(game=game, user=reported.user, sandbox=True)
        self._report(authenticated_client, reported)

        response = self._report(authenticated_client, other_seat)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["code"] == "already_reported"

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
            {"reason": ReportReason.MULTIPLE_ACCOUNTS},
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
    def test_note_required_for_other(self, authenticated_client, reported):
        response = self._report(
            authenticated_client, reported, reason=ReportReason.OTHER, note="  "
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "note" in response.data
        assert Report.objects.count() == 0

    @pytest.mark.django_db
    def test_other_with_note(self, authenticated_client, reported):
        response = self._report(
            authenticated_client,
            reported,
            reason=ReportReason.OTHER,
            note="Spamming links in every channel.",
        )

        assert response.status_code == status.HTTP_201_CREATED

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
