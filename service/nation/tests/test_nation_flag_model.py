import pytest

from nation.models import NationFlag


@pytest.mark.django_db
def test_save_computes_content_hash(draft_variant_for_primary, minimal_flag_svg):
    nation = draft_variant_for_primary.nations.get(nation_id="reds")
    flag = NationFlag.objects.create(nation=nation, svg=minimal_flag_svg)
    assert flag.content_hash
    assert len(flag.content_hash) == 64


@pytest.mark.django_db
def test_save_sanitizes_svg(draft_variant_for_primary):
    nation = draft_variant_for_primary.nations.get(nation_id="reds")
    flag = NationFlag.objects.create(
        nation=nation,
        svg='<svg xmlns="http://www.w3.org/2000/svg"><script>x</script><rect id="r" onclick="x"/></svg>',
    )
    assert "<script" not in flag.svg
    assert "onclick" not in flag.svg
    assert 'id="r"' in flag.svg


@pytest.mark.django_db
def test_one_flag_per_nation(draft_variant_for_primary, minimal_flag_svg):
    nation = draft_variant_for_primary.nations.get(nation_id="reds")
    NationFlag.objects.create(nation=nation, svg=minimal_flag_svg)
    with pytest.raises(Exception):
        NationFlag.objects.create(nation=nation, svg=minimal_flag_svg)
