import pytest
from django.contrib import admin
from django.core.cache import cache
from django.test import override_settings

from common.constants import ProvinceType
from province.models import Province
from variant.models import Variant

LOCMEM_CACHE = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}


@pytest.fixture
def locmem_cache():
    with override_settings(CACHES=LOCMEM_CACHE):
        cache.clear()
        yield
        cache.clear()


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
@pytest.mark.usefixtures("locmem_cache")
class TestCachedForVariant:

    def test_returns_every_province_in_the_variant(self, classical_variant):
        provinces = Province.objects.cached_for_variant(classical_variant)

        assert {province.province_id for province in provinces} == set(
            classical_variant.provinces.values_list("province_id", flat=True)
        )

    def test_loads_parents_with_provinces(
        self, classical_variant, django_assert_num_queries
    ):
        with django_assert_num_queries(1):
            provinces = Province.objects.cached_for_variant(classical_variant)
            spain_nc = next(
                province for province in provinces if province.province_id == "spa/nc"
            )
            assert spain_nc.parent.province_id == "spa"

    def test_repeat_call_is_served_from_cache(
        self, classical_variant, django_assert_num_queries
    ):
        Province.objects.cached_for_variant(classical_variant)

        with django_assert_num_queries(0):
            provinces = Province.objects.cached_for_variant(classical_variant)
            spain_nc = next(
                province for province in provinces if province.province_id == "spa/nc"
            )
            assert spain_nc.parent.province_id == "spa"

        assert len(provinces) == classical_variant.provinces.count()

    def test_variant_update_invalidates_cache(
        self, classical_variant, django_assert_num_queries
    ):
        Province.objects.cached_for_variant(classical_variant)
        classical_variant.save()

        with django_assert_num_queries(1):
            Province.objects.cached_for_variant(classical_variant)


@pytest.mark.django_db
@pytest.mark.usefixtures("locmem_cache")
class TestProvinceAdminCacheInvalidation:

    @pytest.mark.parametrize("change", [False, True])
    def test_save_invalidates_cache(
        self, classical_variant, django_assert_num_queries, change
    ):
        province = Province(
            variant=classical_variant,
            province_id="new",
            name="New province",
            type=ProvinceType.LAND,
        )
        if change:
            province.save()
        Province.objects.cached_for_variant(classical_variant)
        province.name = "Renamed province"

        admin.site._registry[Province].save_model(None, province, None, change)

        variant = Variant.objects.get(pk=classical_variant.pk)
        with django_assert_num_queries(1):
            provinces = Province.objects.cached_for_variant(variant)
        assert (
            next(cached.name for cached in provinces if cached.pk == province.pk)
            == "Renamed province"
        )

    def test_moving_province_invalidates_both_variants(
        self, classical_variant, italy_vs_germany_variant
    ):
        province = Province.objects.create(
            variant=classical_variant,
            province_id="new",
            name="New province",
            type=ProvinceType.LAND,
        )
        Province.objects.cached_for_variant(classical_variant)
        Province.objects.cached_for_variant(italy_vs_germany_variant)
        province.variant = italy_vs_germany_variant

        admin.site._registry[Province].save_model(None, province, None, True)

        original_variant = Variant.objects.get(pk=classical_variant.pk)
        new_variant = Variant.objects.get(pk=italy_vs_germany_variant.pk)
        assert province.pk not in {
            province.pk
            for province in Province.objects.cached_for_variant(original_variant)
        }
        assert province.pk in {
            province.pk for province in Province.objects.cached_for_variant(new_variant)
        }

    @pytest.mark.parametrize("bulk", [False, True])
    def test_delete_invalidates_cache(
        self,
        classical_variant,
        classical_wales_province,
        django_assert_num_queries,
        bulk,
    ):
        Province.objects.cached_for_variant(classical_variant)
        province_id = classical_wales_province.pk
        province_admin = admin.site._registry[Province]

        if bulk:
            province_admin.delete_queryset(
                None, Province.objects.filter(pk=province_id)
            )
        else:
            province_admin.delete_model(None, classical_wales_province)

        variant = Variant.objects.get(pk=classical_variant.pk)
        with django_assert_num_queries(1):
            provinces = Province.objects.cached_for_variant(variant)
        assert province_id not in {province.pk for province in provinces}
