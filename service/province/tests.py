import pytest

from province.models import Province


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
