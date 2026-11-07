import pytest
from django.core.cache import cache
from django.db import connection
from django.test.utils import override_settings

from province.models import Province

LOCMEM_CACHE = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}


class TestHomeNationBackfill:

    @pytest.mark.django_db
    def test_home_center_resolves_to_owning_nation(self, classical_variant):
        london = Province.objects.get(province_id="lon", variant=classical_variant)
        paris = Province.objects.get(province_id="par", variant=classical_variant)

        assert london.home_nation.name == "England"
        assert paris.home_nation.name == "France"

    @pytest.mark.django_db
    def test_neutral_supply_center_has_no_home_nation(self, classical_variant):
        belgium = Province.objects.get(province_id="bel", variant=classical_variant)

        assert belgium.supply_center is True
        assert belgium.home_nation is None

    @pytest.mark.django_db
    def test_non_supply_center_province_has_no_home_nation(self, classical_variant):
        wales = Province.objects.get(province_id="wal", variant=classical_variant)

        assert wales.supply_center is False
        assert wales.home_nation is None


class TestAdjacencyBackfill:

    @pytest.mark.django_db
    def test_adjacencies_backfilled(self, classical_variant):
        stp = Province.objects.get(province_id="stp", variant=classical_variant)

        assert stp.adjacencies == [
            {"to": "bar", "pass": "fleet"},
            {"to": "bot", "pass": "fleet"},
            {"to": "fin", "pass": "army"},
            {"to": "lvn", "pass": "army"},
            {"to": "mos", "pass": "army"},
            {"to": "nwy", "pass": "army"},
        ]

    @pytest.mark.django_db
    def test_every_province_has_adjacencies(self):
        assert not Province.objects.filter(adjacencies=[]).exists()

    @pytest.mark.django_db
    def test_adjacencies_are_symmetric(self):
        variant_ids = Province.objects.values_list("variant_id", flat=True).distinct()
        for variant_id in variant_ids:
            edges = {
                (province.province_id, adjacency["to"], adjacency["pass"])
                for province in Province.objects.filter(variant_id=variant_id)
                for adjacency in province.adjacencies
            }
            for source, target, pass_ in edges:
                assert (target, source, pass_) in edges, (
                    f"{variant_id}: {source} -> {target} ({pass_}) "
                    f"is not mirrored on the other side"
                )


@pytest.mark.django_db
class TestCachedForVariant:

    @pytest.fixture(autouse=True)
    def locmem_cache(self):
        with override_settings(CACHES=LOCMEM_CACHE):
            cache.clear()
            yield
            cache.clear()

    def _query_count(self, variant):
        connection.queries_log.clear()
        with override_settings(DEBUG=True):
            provinces = Province.objects.cached_for_variant(variant)
            [province.parent and province.parent.province_id for province in provinces]
        return len(connection.queries), provinces

    def test_returns_every_province_in_the_variant(self, classical_variant):
        provinces = Province.objects.cached_for_variant(classical_variant)

        assert {province.province_id for province in provinces} == set(
            classical_variant.provinces.values_list("province_id", flat=True)
        )

    def test_loads_parents_with_provinces(self, classical_variant):
        query_count, provinces = self._query_count(classical_variant)

        assert query_count == 1
        spain_nc = next(p for p in provinces if p.province_id == "spa/nc")
        assert spain_nc.parent.province_id == "spa"

    def test_repeat_call_is_served_from_cache(self, classical_variant):
        Province.objects.cached_for_variant(classical_variant)

        query_count, provinces = self._query_count(classical_variant)

        assert query_count == 0
        assert len(provinces) == classical_variant.provinces.count()

    def test_variant_update_invalidates_cache(self, classical_variant):
        Province.objects.cached_for_variant(classical_variant)
        classical_variant.save()

        query_count, _ = self._query_count(classical_variant)

        assert query_count == 1
