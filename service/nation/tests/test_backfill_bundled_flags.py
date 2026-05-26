import pytest

from nation.models import NationFlag


@pytest.mark.django_db
def test_classical_nations_have_flags_from_backfill(classical_variant):
    nations = list(classical_variant.nations.all())
    assert nations
    flags = NationFlag.objects.filter(nation__variant=classical_variant)
    assert flags.count() == len(nations)


@pytest.mark.django_db
def test_italy_vs_germany_reuses_classical_flags(db):
    classical_germany = NationFlag.objects.get(
        nation__variant_id="classical", nation__nation_id="germany"
    )
    ivg_germany = NationFlag.objects.get(
        nation__variant_id="italy-vs-germany", nation__nation_id="germany"
    )
    assert classical_germany.content_hash == ivg_germany.content_hash
