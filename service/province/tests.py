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
        variant_ids = Province.objects.values_list(
            "variant_id", flat=True
        ).distinct()
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
