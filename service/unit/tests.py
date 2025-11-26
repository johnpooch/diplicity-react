import pytest
from django.test.utils import override_settings
from django.db import connection
from common.constants import PhaseStatus, GameStatus
from game.models import Game


class TestUnitAdminQueryPerformance:

    @pytest.mark.django_db
    def test_admin_changelist_query_count_simple(
        self,
        authenticated_client,
        primary_user,
        classical_variant,
        classical_england_nation,
        classical_edinburgh_province,
    ):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)

        game = Game.objects.create(
            name="Simple Test Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
        )
        phase = game.phases.create(
            game=game,
            variant=classical_variant,
            season="Spring",
            year=1901,
            type="Movement",
            status=PhaseStatus.ACTIVE,
            ordinal=1,
        )
        phase.units.create(
            type="Fleet",
            nation=classical_england_nation,
            province=classical_edinburgh_province,
        )

        url = "/admin/unit/unit/"
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == 200

        unit_queries = [q for q in connection.queries if '"unit_unit"' in q['sql'] and 'SELECT "unit_unit"."id"' in q['sql']]

        assert len(unit_queries) == 1
        assert 'INNER JOIN "nation_nation"' in unit_queries[0]['sql']
        assert 'INNER JOIN "province_province"' in unit_queries[0]['sql']
        assert 'INNER JOIN "phase_phase"' in unit_queries[0]['sql']
        assert 'LEFT OUTER JOIN "unit_unit"' in unit_queries[0]['sql']

    @pytest.mark.django_db
    def test_admin_changelist_query_count_with_multiple_phases_and_units(
        self,
        authenticated_client,
        db,
        classical_variant,
        primary_user,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
        classical_london_province,
        classical_paris_province,
    ):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)

        for i in range(4):
            game = Game.objects.create(
                name=f"Game with Units {i}",
                variant=classical_variant,
                status=GameStatus.ACTIVE,
            )

            for j in range(2):
                phase = game.phases.create(
                    game=game,
                    variant=classical_variant,
                    season="Spring" if j == 0 else "Fall",
                    year=1901,
                    type="Movement",
                    status=PhaseStatus.ACTIVE if j == 1 else PhaseStatus.COMPLETED,
                    ordinal=j + 1,
                )
                phase.units.create(
                    type="Fleet",
                    nation=classical_england_nation,
                    province=classical_edinburgh_province,
                )
                phase.units.create(
                    type="Army",
                    nation=classical_england_nation,
                    province=classical_london_province,
                )
                phase.units.create(
                    type="Army",
                    nation=classical_france_nation,
                    province=classical_paris_province,
                )

        url = "/admin/unit/unit/"
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == 200

        unit_queries = [q for q in connection.queries if '"unit_unit"' in q['sql'] and 'SELECT "unit_unit"."id"' in q['sql']]

        assert len(unit_queries) == 1
        assert 'INNER JOIN "nation_nation"' in unit_queries[0]['sql']
        assert 'INNER JOIN "province_province"' in unit_queries[0]['sql']
        assert 'INNER JOIN "phase_phase"' in unit_queries[0]['sql']
        assert 'LEFT OUTER JOIN "unit_unit"' in unit_queries[0]['sql']

    @pytest.mark.django_db
    def test_admin_changelist_query_count_with_dislodged_units(
        self,
        authenticated_client,
        db,
        classical_variant,
        primary_user,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
        classical_london_province,
        classical_paris_province,
    ):
        primary_user.is_staff = True
        primary_user.is_superuser = True
        primary_user.save()
        authenticated_client.force_login(primary_user)

        for i in range(3):
            game = Game.objects.create(
                name=f"Game with Dislodged Units {i}",
                variant=classical_variant,
                status=GameStatus.ACTIVE,
            )

            phase = game.phases.create(
                game=game,
                variant=classical_variant,
                season="Spring",
                year=1901,
                type="Movement",
                status=PhaseStatus.ACTIVE,
                ordinal=1,
            )

            attacking_unit = phase.units.create(
                type="Fleet",
                nation=classical_france_nation,
                province=classical_paris_province,
            )
            phase.units.create(
                type="Army",
                nation=classical_england_nation,
                province=classical_london_province,
                dislodged_by=attacking_unit,
            )
            phase.units.create(
                type="Fleet",
                nation=classical_england_nation,
                province=classical_edinburgh_province,
            )

        url = "/admin/unit/unit/"
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == 200

        unit_queries = [q for q in connection.queries if '"unit_unit"' in q['sql'] and 'SELECT "unit_unit"."id"' in q['sql']]

        assert len(unit_queries) == 1
        assert 'INNER JOIN "nation_nation"' in unit_queries[0]['sql']
        assert 'INNER JOIN "province_province"' in unit_queries[0]['sql']
        assert 'INNER JOIN "phase_phase"' in unit_queries[0]['sql']
        assert 'LEFT OUTER JOIN "unit_unit"' in unit_queries[0]['sql']
