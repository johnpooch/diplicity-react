import copy
import json
import re
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from common.constants import PhaseStatus, VariantStatus
from phase.models import Phase
from django.urls import reverse
from django.test.utils import override_settings
from django.db import connection
from rest_framework import status

from adjudicator.serializers import deserialize_variant, VariantValidationError
from variant.models import Variant, default_phase_progression
from variant.utils import normalize_dsvg, variant_to_canonical_dict

IN_DB_VARIANT_IDS = {
    "classical", "italy-vs-germany", "hundred",
    "youngstown-redux", "vietnam-war", "canton",
}

viewname = "variant-list"


@pytest.mark.django_db
def test_list_variants_success(authenticated_client, classical_variant):
    url = reverse(viewname)
    response = authenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 6

    variants_by_id = {v["id"]: v for v in response.data}
    assert variants_by_id[classical_variant.id]["name"] == classical_variant.name
    assert variants_by_id["italy-vs-germany"]["name"] == "Italy vs Germany"

    classical_variant_data = variants_by_id[classical_variant.id]

    assert "rules" in classical_variant_data
    assert classical_variant_data["rules"].startswith("The first to 18 Supply Centers")

    assert classical_variant_data["victory_conditions"] == {
        "solo_victory_supply_centers": 18,
        "game_ends_year": None,
        "draw_after_year": None,
    }

    assert "template_phase" in classical_variant_data
    template_phase = classical_variant_data["template_phase"]

    assert "year" in template_phase
    assert "units" in template_phase
    assert "supply_centers" in template_phase
    assert isinstance(template_phase["units"], list)
    assert isinstance(template_phase["supply_centers"], list)

    # Check that we have the expected number of units and supply centers
    assert len(template_phase["units"]) > 0
    assert len(template_phase["supply_centers"]) > 0


@pytest.mark.django_db
def test_list_variants_unauthenticated(unauthenticated_client, classical_variant, user_factory):
    draft_variant = Variant.objects.create(
        id="vis-draft", name="Visibility Draft", description="",
        status=VariantStatus.DRAFT, owner=user_factory(),
    )
    url = reverse(viewname)
    response = unauthenticated_client.get(url)
    assert response.status_code == status.HTTP_200_OK
    ids = {v["id"] for v in response.data}
    assert classical_variant.id in ids
    assert draft_variant.id not in ids


@pytest.mark.django_db
def test_list_variants_cache_control_allows_public_caching(authenticated_client):
    response = authenticated_client.get(reverse(viewname))

    assert response["Cache-Control"] == "public"


@pytest.mark.django_db
def test_list_variants_returns_304_when_etag_matches(authenticated_client):
    response1 = authenticated_client.get(reverse(viewname))
    etag = response1["ETag"]

    response2 = authenticated_client.get(reverse(viewname), HTTP_IF_NONE_MATCH=etag)

    assert response2.status_code == status.HTTP_304_NOT_MODIFIED


@pytest.mark.django_db
def test_list_variants_returns_304_when_weakened_etag_matches(authenticated_client):
    response1 = authenticated_client.get(reverse(viewname))
    etag = response1["ETag"]

    response2 = authenticated_client.get(reverse(viewname), HTTP_IF_NONE_MATCH=f"W/{etag}")

    assert response2.status_code == status.HTTP_304_NOT_MODIFIED


@pytest.mark.django_db
def test_list_variants_returns_200_when_weakened_etag_is_stale(authenticated_client):
    response = authenticated_client.get(reverse(viewname), HTTP_IF_NONE_MATCH='W/"stale"')

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_retrieve_variant_returns_304_when_weakened_etag_matches(authenticated_client):
    url = reverse("variant-detail", args=["classical"])
    etag = authenticated_client.get(url)["ETag"]

    response = authenticated_client.get(url, HTTP_IF_NONE_MATCH=f"W/{etag}")

    assert response.status_code == status.HTTP_304_NOT_MODIFIED


@pytest.mark.django_db
def test_list_variants_includes_svg_url(authenticated_client):
    response = authenticated_client.get(reverse(viewname))

    classical = {v["id"]: v for v in response.data}["classical"]
    assert classical["svg_url"] is not None
    assert "/variants/classical/svg/" in classical["svg_url"]
    assert classical["svg_url"].endswith(".svg")


@pytest.mark.django_db
def test_svg_url_is_null_when_variant_has_no_svg(authenticated_client):
    Variant.objects.create(id="no-svg", name="No SVG", description="", author="", status=VariantStatus.PUBLISHED)

    response = authenticated_client.get(reverse(viewname))

    no_svg = {v["id"]: v for v in response.data}["no-svg"]
    assert no_svg["svg_url"] is None


class TestVariantListViewQueryPerformance:

    @pytest.mark.django_db
    def test_list_variants_query_count_with_all_variants(self, authenticated_client, classical_variant):
        """Test query count when listing all variants (classical + italy-vs-germany)."""
        url = reverse(viewname)
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 6

        # With optimized queries, we should have a constant number of queries
        # regardless of the number of variants due to prefetch_related
        query_count = len(connection.queries)

        # 18 prefetch queries + 2 ETag aggregates (Variant + NationFlag max
        # updated_at). This is the cache-miss path; hits skip the 18.
        assert query_count == 20

    @pytest.mark.django_db
    def test_list_variants_query_count_with_single_variant(self, authenticated_client, classical_variant):
        """Test query count when only one variant exists (by creating a fresh test)."""
        # Create a new variant to test with a single variant scenario

        # Create a minimal test variant
        test_variant = Variant.objects.create(
            id="test-single-variant",
            name="Test Single Variant",
            description="A test variant for query optimization testing",
            author="Test",
            status=VariantStatus.PUBLISHED,
        )

        # Create a template phase for the test variant
        Phase.objects.create(
            variant=test_variant, season="Spring", year=1901, type="Movement", status=PhaseStatus.TEMPLATE, ordinal=1
        )

        url = reverse(viewname)
        connection.queries_log.clear()

        with override_settings(DEBUG=True):
            response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Should have at least 4 variants now (classical, hundred, italy-vs-germany, youngstown-redux, test-single-variant)
        assert len(response.data) >= 5

        # Should have the same number of queries regardless of variant count
        # due to prefetch_related optimization
        query_count = len(connection.queries)
        # 18 prefetch queries + 2 ETag aggregates (Variant + NationFlag max
        # updated_at). This is the cache-miss path; hits skip the 18.
        assert query_count == 20


class TestPhaseProgressionBackfill:

    @pytest.mark.django_db
    def test_classical_phase_progression(self, classical_variant):
        assert classical_variant.phase_progression == default_phase_progression()

    @pytest.mark.django_db
    def test_hundred_phase_progression(self, hundred_variant):
        progression = hundred_variant.phase_progression
        assert progression["seasons"] == ["Year"]

        adjustment_to_movement = next(
            t for t in progression["transitions"]
            if t["from"]["type"] == "Adjustment"
        )
        assert adjustment_to_movement["to"]["type"] == "Movement"
        assert adjustment_to_movement["to"]["yearDelta"] == 5

    @pytest.mark.django_db
    def test_every_variant_has_phase_progression(self, classical_variant):
        assert not Variant.objects.filter(phase_progression={}).exists()
        for variant in Variant.objects.all():
            assert variant.phase_progression["seasons"]
            assert variant.phase_progression["transitions"]


class TestRulesBackfill:

    @pytest.mark.django_db
    def test_classical_rules(self, classical_variant):
        assert classical_variant.rules == (
            "The first to 18 Supply Centers (SC) is the winner.\n"
            "Kiel and Constantinople have a canal, so fleets can exit on either side.\n"
            "Armies can move from Denmark to Kiel."
        )

    @pytest.mark.django_db
    def test_hundred_rules(self, hundred_variant):
        assert hundred_variant.rules.startswith(
            "First to 9 Supply Centers (SC) is the winner."
        )

    @pytest.mark.django_db
    def test_every_in_db_variant_has_rules(self, classical_variant):
        for variant in Variant.objects.filter(id__in=IN_DB_VARIANT_IDS):
            assert variant.rules


class TestAdjudicationModifiers:

    @pytest.mark.django_db
    def test_hundred_allows_non_home_builds(self, hundred_variant):
        assert "allow-builds-in-non-home-centers" in (
            hundred_variant.adjudication_modifiers
        )

    @pytest.mark.django_db
    def test_classical_has_no_modifiers(self, classical_variant):
        assert classical_variant.adjudication_modifiers == []


class TestSupplyCenterTargetDeserialization:

    @pytest.mark.django_db
    def test_nation_override_accepted(self, classical_variant):
        canonical = copy.deepcopy(variant_to_canonical_dict(classical_variant))
        canonical["victoryConditions"].append(
            {"type": "supply-center-majority", "supplyCenters": 15, "nation": "england"}
        )
        variant = deserialize_variant(canonical)
        assert [(c.supply_centers, c.nation) for c in variant.victory_conditions] == [(18, None), (15, "england")]

    @pytest.mark.django_db
    @pytest.mark.parametrize(
        "extra,match",
        [
            pytest.param(
                [{"type": "supply-center-majority", "supplyCenters": 20}],
                "Duplicate default",
                id="duplicate_default",
            ),
            pytest.param(
                [
                    {"type": "supply-center-majority", "supplyCenters": 15, "nation": "england"},
                    {"type": "supply-center-majority", "supplyCenters": 16, "nation": "england"},
                ],
                "Duplicate supply-center-majority victory condition for nation 'england'",
                id="duplicate_override",
            ),
            pytest.param(
                [{"type": "supply-center-majority", "supplyCenters": 15, "nation": "atlantis"}],
                "unknown nation 'atlantis'",
                id="unknown_nation",
            ),
        ],
    )
    def test_invalid_supply_center_targets_rejected(self, classical_variant, extra, match):
        canonical = copy.deepcopy(variant_to_canonical_dict(classical_variant))
        canonical["victoryConditions"].extend(extra)
        with pytest.raises(VariantValidationError, match=match):
            deserialize_variant(canonical)

    @pytest.mark.django_db
    def test_non_playable_nation_override_rejected(self, classical_variant):
        canonical = copy.deepcopy(variant_to_canonical_dict(classical_variant))
        for nation in canonical["nations"]:
            if nation["id"] == "england":
                nation["non_playable"] = True
        canonical["victoryConditions"].append(
            {"type": "supply-center-majority", "supplyCenters": 15, "nation": "england"}
        )
        with pytest.raises(VariantValidationError, match="non-playable nation 'england'"):
            deserialize_variant(canonical)


class TestVariantToCanonicalDict:

    @pytest.mark.django_db
    def test_round_trips_every_in_db_variant(self, classical_variant):
        variants = list(Variant.objects.filter(id__in=IN_DB_VARIANT_IDS))
        assert len(variants) == len(IN_DB_VARIANT_IDS)
        for variant in variants:
            canonical = variant_to_canonical_dict(variant)
            deserialize_variant(canonical)

    @pytest.mark.django_db
    def test_query_count_does_not_scale_with_variant_size(self, classical_variant):
        connection.queries_log.clear()
        with override_settings(DEBUG=True):
            variant_to_canonical_dict(Variant.objects.get(pk="italy-vs-germany"))
        small_count = len(connection.queries)

        connection.queries_log.clear()
        with override_settings(DEBUG=True):
            variant_to_canonical_dict(Variant.objects.get(pk="classical"))
        large_count = len(connection.queries)

        assert small_count == large_count == 6

    @pytest.mark.django_db
    def test_query_count_does_not_scale_with_phase_history(self, classical_variant):
        from common.constants import GameStatus
        from game.models import Game

        for i in range(5):
            game = Game.objects.create(variant=classical_variant, name=f"g{i}", status=GameStatus.ACTIVE)
            Phase.objects.create(
                game=game, variant=classical_variant, ordinal=1,
                season="Spring", year=1901, type="Movement", status=PhaseStatus.ACTIVE,
            )

        connection.queries_log.clear()
        with override_settings(DEBUG=True):
            variant_to_canonical_dict(Variant.objects.get(pk="classical"))

        assert len(connection.queries) == 6

    @pytest.mark.django_db
    def test_classical_structure(self, classical_variant):
        canonical = variant_to_canonical_dict(classical_variant)

        assert canonical["schemaVersion"] == 1
        assert canonical["id"] == "classical"
        assert canonical["victoryConditions"] == [
            {"type": "supply-center-majority", "supplyCenters": 18}
        ]

        # Named coasts are split out of provinces into their own collection.
        province_types = {p["type"] for p in canonical["provinces"]}
        assert province_types <= {"land", "sea", "coastal"}
        named_coast_ids = {nc["id"] for nc in canonical["namedCoasts"]}
        assert named_coast_ids == {"stp/nc", "stp/sc", "bul/ec", "bul/sc", "spa/nc", "spa/sc"}
        for named_coast in canonical["namedCoasts"]:
            assert named_coast["parentProvince"] == named_coast["id"].split("/")[0]

        home_nations = {p["id"]: p["homeNation"] for p in canonical["provinces"] if "homeNation" in p}
        assert home_nations["par"] == "france"

        initial_state = canonical["initialState"]
        assert initial_state["phase"] == {"season": "Spring", "year": 1901, "type": "Movement"}
        assert len(initial_state["units"]) == 22
        assert len(initial_state["supplyCenters"]) == 22

    @pytest.mark.django_db
    def test_neutral_nations_auto_build_modifier_accepted(self, classical_variant):
        canonical = variant_to_canonical_dict(classical_variant)
        canonical["adjudicationModifiers"] = ["neutral-nations-auto-build"]
        deserialize_variant(canonical)

    @pytest.mark.django_db
    def test_any_home_center_builds_modifier_accepted(self, classical_variant):
        canonical = variant_to_canonical_dict(classical_variant)
        canonical["adjudicationModifiers"] = ["allow-builds-in-any-home-center"]
        deserialize_variant(canonical)

    @pytest.mark.django_db
    def test_unknown_modifier_raises_variant_validation_error(self, classical_variant):
        canonical = variant_to_canonical_dict(classical_variant)
        canonical["adjudicationModifiers"] = ["not-a-real-modifier"]
        with pytest.raises(VariantValidationError, match="Unknown adjudication modifier"):
            deserialize_variant(canonical)


@pytest.mark.django_db
def test_published_variant_visible_to_any_user(authenticated_client):
    response = authenticated_client.get(reverse(viewname))
    assert response.status_code == status.HTTP_200_OK
    ids = {v["id"] for v in response.data}
    assert "classical" in ids


@pytest.mark.django_db
def test_own_draft_hidden_from_list(user_factory, authenticated_client_factory):
    owner = user_factory()
    owner_client = authenticated_client_factory(owner)
    draft_variant = Variant.objects.create(
        id="vis-draft", name="Visibility Draft", description="",
        status=VariantStatus.DRAFT, owner=owner,
    )
    response = owner_client.get(reverse(viewname))
    ids = {v["id"] for v in response.data}
    assert draft_variant.id not in ids


@pytest.mark.django_db
def test_other_users_draft_hidden_from_list(authenticated_client, user_factory):
    owner = user_factory()
    draft_variant = Variant.objects.create(
        id="vis-draft", name="Visibility Draft", description="",
        status=VariantStatus.DRAFT, owner=owner,
    )
    response = authenticated_client.get(reverse(viewname))
    ids = {v["id"] for v in response.data}
    assert draft_variant.id not in ids


@pytest.mark.django_db
def test_other_users_draft_returns_404_on_detail(authenticated_client, user_factory):
    owner = user_factory()
    draft_variant = Variant.objects.create(
        id="vis-draft", name="Visibility Draft", description="",
        status=VariantStatus.DRAFT, owner=owner,
    )
    response = authenticated_client.get(reverse("variant-detail", kwargs={"pk": draft_variant.id}))
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_archived_variant_hidden_from_list(authenticated_client):
    Variant.objects.create(
        id="vis-archived", name="Visibility Archived", description="",
        status=VariantStatus.ARCHIVED,
    )
    response = authenticated_client.get(reverse(viewname))
    ids = {v["id"] for v in response.data}
    assert "vis-archived" not in ids


@pytest.mark.django_db
def test_member_of_draft_variant_game_does_not_see_variant_in_list(
    user_factory, authenticated_client_factory, game_factory, member_factory
):
    owner = user_factory()
    other_user = user_factory()
    other_client = authenticated_client_factory(other_user)
    draft_variant = Variant.objects.create(
        id="vis-draft", name="Visibility Draft", description="",
        status=VariantStatus.DRAFT, owner=owner,
    )
    game = game_factory(variant=draft_variant, private=True)
    member_factory(game=game, user=other_user)
    response = other_client.get(reverse(viewname))
    ids = {v["id"] for v in response.data}
    assert draft_variant.id not in ids


@pytest.mark.django_db
def test_member_of_draft_variant_game_can_retrieve_variant(
    user_factory, authenticated_client_factory, game_factory, member_factory
):
    owner = user_factory()
    other_user = user_factory()
    other_client = authenticated_client_factory(other_user)
    draft_variant = Variant.objects.create(
        id="vis-draft", name="Visibility Draft", description="",
        status=VariantStatus.DRAFT, owner=owner,
    )
    game = game_factory(variant=draft_variant, private=True)
    member_factory(game=game, user=other_user)
    response = other_client.get(reverse("variant-detail", kwargs={"pk": draft_variant.id}))
    assert response.status_code == status.HTTP_200_OK


class TestNationColor:

    @pytest.mark.django_db
    def test_returns_raw_variant_colors(
        self, user_factory, authenticated_client_factory, classical_variant
    ):
        user = user_factory()
        client = authenticated_client_factory(user)

        response = client.get(reverse(viewname))

        classical = {v["id"]: v for v in response.data}["classical"]
        nations_by_id = {n["nation_id"]: n for n in classical["nations"]}
        assert nations_by_id["england"]["color"] == "#2196F3"
        assert nations_by_id["italy"]["color"] == "#4CAF50"


COMMITTED_DSVGS = sorted((Path(__file__).resolve().parent / "data" / "svg").glob("*.d.svg"))

UNSAFE_DSVG_PAYLOADS = [
    ('<a xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="java&#x09;script:alert(1)"><rect/></a>', "alert("),
    ('<animate attributeName="href" values="javascript:alert(1)"/>', "alert("),
    ('<set attributeName="href" from="javascript:alert(1)"/>', "alert("),
    ('<rect onclick="alert(1)"/>', "alert("),
    ("<script>alert(1)</script>", "alert("),
    ('<foreignObject><div xmlns="http://www.w3.org/1999/xhtml">alert(1)</div></foreignObject>', "alert("),
    ('<a href="data:text/html,alert(1)"><rect/></a>', "alert("),
    ('<use href="https://evil.example/sprite.svg#a"/>', "evil.example"),
    ('<rect style="fill:url(https://evil.example/a.png)"/>', "evil.example"),
    ("<style>@import url(https://evil.example/x.css);</style>", "evil.example"),
    ('<style>.a{fill:url(https://evil.example/a.png)}</style><rect class="a"/>', "evil.example"),
    ('<style>.a{fill:u\\72l(https://evil.example/a.png)}</style><rect class="a"/>', "evil.example"),
    ('<style>.a{fill:expression(alert(1))}</style><rect class="a"/>', "alert("),
    ('<style>@import url(https://evil.example/x.css);.a{fill:#fff}</style><rect class="a"/>', "evil.example"),
    ('<style>.a{fill:#fff}body{fill:#123456}</style><rect class="a"/>', "#123456"),
    ('<style>.a{fill:#fff}*{fill:#654321}</style><rect class="a"/>', "#654321"),
]

FONT_FACE_WITH_UNICODE_RANGE = """
@font-face {
  font-family: 'Libre Baskerville';
  font-style: normal;
  font-weight: 700;
  src: url('data:font/woff2;charset=utf-8;base64,AAAA') format('woff2');
  unicode-range: U+2e, U+41-59, U+61-70, U+72-7a;
}
"""


def _variant_upload(dvar, dsvg):
    return {
        "dvar": SimpleUploadedFile("upload.dvar.json", json.dumps(dvar).encode(), "application/json"),
        "dsvg": SimpleUploadedFile("upload.svg", dsvg.encode(), "image/svg+xml"),
    }


def _with_foreground_content(dsvg, content):
    injected, count = re.subn(
        r'(<g\b[^>]*\bid="foreground"[^>]*>)', lambda match: match.group(1) + content, dsvg, count=1
    )
    assert count == 1
    return injected


def _draft_dvar(dvar, slug):
    draft = copy.deepcopy(dvar)
    draft["id"] = slug
    return draft


@pytest.mark.django_db
class TestVariantListCreateView:
    @pytest.mark.parametrize("payload, marker", UNSAFE_DSVG_PAYLOADS)
    def test_create_removes_unsafe_svg_content(
        self, authenticated_client, classical_dvar, classical_dsvg, payload, marker
    ):
        response = authenticated_client.post(
            reverse("variant-list"),
            _variant_upload(
                _draft_dvar(classical_dvar, "unsafe-draft"), _with_foreground_content(classical_dsvg, payload)
            ),
            format="multipart",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data

        served = authenticated_client.get(response.data["svg_url"]).content.decode()
        assert marker not in served
        assert 'id="foreground"' in served

    def test_create_keeps_font_faces_and_inlines_class_rules(
        self, authenticated_client, classical_dvar, classical_dsvg
    ):
        content = (
            "<style>.label{text-anchor:middle;paint-order:stroke;stroke:#fff;stroke-width:3;stroke-linejoin:round}"
            f".B{{fill:#FFCD00}}.C{{stroke:none}}{FONT_FACE_WITH_UNICODE_RANGE}</style>"
            '<text id="label-text" class="label">Paris</text>'
            '<path id="label-path" class="B C label" d="M0 0h1" style="stroke-width:5.448"/>'
            '<filter id="label-filter" color-interpolation-filters="sRGB" shape-rendering="crispEdges"/>'
        )
        response = authenticated_client.post(
            reverse("variant-list"),
            _variant_upload(
                _draft_dvar(classical_dvar, "styled-draft"), _with_foreground_content(classical_dsvg, content)
            ),
            format="multipart",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data

        served = authenticated_client.get(response.data["svg_url"]).content.decode()
        assert f"<style>{FONT_FACE_WITH_UNICODE_RANGE}</style>" in served
        assert (
            '<text id="label-text" style="text-anchor:middle;paint-order:stroke;stroke:#fff;'
            'stroke-width:3;stroke-linejoin:round">Paris</text>'
        ) in served
        assert (
            '<path id="label-path" d="M0 0h1" style="text-anchor:middle;paint-order:stroke;stroke:none;'
            'stroke-linejoin:round;fill:#FFCD00;stroke-width:5.448"/>'
        ) in served
        assert '<filter id="label-filter" color-interpolation-filters="sRGB" shape-rendering="crispEdges"/>' in served
        assert "class=" not in served

    def test_create_rejects_non_svg_root(self, authenticated_client, classical_dvar):
        response = authenticated_client.post(
            reverse("variant-list"),
            _variant_upload(_draft_dvar(classical_dvar, "html-draft"), '<html xmlns="http://www.w3.org/1999/xhtml"/>'),
            format="multipart",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["dsvg"] == [
            {"code": "INVALID_ROOT", "message": "Root element must be <svg> in the SVG namespace."}
        ]

    @pytest.mark.parametrize("dsvg_path", COMMITTED_DSVGS, ids=lambda path: path.name)
    def test_committed_maps_keep_their_rendering(self, authenticated_client, svg_rendering_signature, dsvg_path):
        variant_id = dsvg_path.name.removesuffix(".d.svg")
        dvar = variant_to_canonical_dict(Variant.objects.get(id=variant_id))
        source = dsvg_path.read_text()

        response = authenticated_client.post(
            reverse("variant-list"),
            _variant_upload(_draft_dvar(dvar, f"{variant_id}-copy"), source),
            format="multipart",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.data

        served = authenticated_client.get(response.data["svg_url"]).content.decode()
        assert svg_rendering_signature(served) == svg_rendering_signature(normalize_dsvg(source))


@pytest.mark.django_db
class TestVariantDetailView:
    @pytest.mark.parametrize("payload, marker", UNSAFE_DSVG_PAYLOADS[:3])
    def test_update_removes_unsafe_svg_content(
        self, authenticated_client, classical_dvar, classical_dsvg, payload, marker
    ):
        dvar = _draft_dvar(classical_dvar, "updated-draft")
        created = authenticated_client.post(
            reverse("variant-list"), _variant_upload(dvar, classical_dsvg), format="multipart"
        )
        assert created.status_code == status.HTTP_201_CREATED, created.data

        response = authenticated_client.put(
            reverse("variant-detail", kwargs={"pk": created.data["id"]}),
            _variant_upload(dvar, _with_foreground_content(classical_dsvg, payload)),
            format="multipart",
        )
        assert response.status_code == status.HTTP_200_OK, response.data

        served = authenticated_client.get(response.data["svg_url"]).content.decode()
        assert marker not in served
