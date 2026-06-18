import copy
import json

import pytest
from django.urls import reverse
from rest_framework import status

from common.constants import VariantStatus
from variant.models import Variant
from variant.utils import variant_to_canonical_dict


@pytest.fixture
def classical_dvar(classical_variant):
    return variant_to_canonical_dict(classical_variant)


@pytest.fixture
def classical_dsvg(classical_variant):
    return classical_variant.svg.svg


def _dvar_upload(dvar, dsvg, dvar_filename="upload.dvar.json", dsvg_filename="upload.svg"):
    from django.core.files.uploadedfile import SimpleUploadedFile

    return {
        "dvar": SimpleUploadedFile(dvar_filename, json.dumps(dvar).encode(), "application/json"),
        "dsvg": SimpleUploadedFile(dsvg_filename, dsvg.encode(), "image/svg+xml"),
    }


@pytest.mark.django_db
def test_create_variant_unauthenticated(unauthenticated_client, classical_dvar, classical_dsvg):
    dvar = copy.deepcopy(classical_dvar)
    dvar["id"] = "my-draft"
    response = unauthenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_create_variant_success(authenticated_client, primary_user, classical_dvar, classical_dsvg):
    dvar = copy.deepcopy(classical_dvar)
    dvar["id"] = "my-draft"
    dvar["name"] = "My Draft"
    response = authenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert response.status_code == status.HTTP_201_CREATED, response.data
    expected_id = f"{primary_user.id}-my-draft"
    assert response.data["id"] == expected_id
    assert response.data["status"] == VariantStatus.DRAFT
    assert response.data["official"] is False

    variant = Variant.objects.get(id=expected_id)
    assert variant.owner_id == primary_user.id
    assert variant.status == VariantStatus.DRAFT
    assert variant.slug == "my-draft"
    assert variant.official is False
    assert variant.nations.count() == len(dvar["nations"])
    assert variant.provinces.filter(parent__isnull=True).count() == len(dvar["provinces"])


@pytest.mark.django_db
def test_create_variant_id_prefixed_with_owner(
    authenticated_client, primary_user, classical_dvar, classical_dsvg
):
    dvar = copy.deepcopy(classical_dvar)
    dvar["id"] = "europe-1939"
    response = authenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert response.status_code == status.HTTP_201_CREATED, response.data
    assert response.data["id"] == f"{primary_user.id}-europe-1939"
    assert Variant.objects.filter(id=f"{primary_user.id}-europe-1939").exists()
    assert not Variant.objects.filter(id="europe-1939").exists()


@pytest.mark.django_db
def test_two_users_can_upload_same_slug(
    authenticated_client,
    authenticated_client_for_secondary_user,
    primary_user,
    secondary_user,
    classical_dvar,
    classical_dsvg,
):
    dvar = copy.deepcopy(classical_dvar)
    dvar["id"] = "shared-slug"

    r1 = authenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert r1.status_code == status.HTTP_201_CREATED, r1.data
    assert r1.data["id"] == f"{primary_user.id}-shared-slug"

    r2 = authenticated_client_for_secondary_user.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert r2.status_code == status.HTTP_201_CREATED, r2.data
    assert r2.data["id"] == f"{secondary_user.id}-shared-slug"


@pytest.mark.django_db
def test_same_user_cannot_upload_same_slug_twice(
    authenticated_client, classical_dvar, classical_dsvg
):
    dvar = copy.deepcopy(classical_dvar)
    dvar["id"] = "duplicate-slug"

    r1 = authenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert r1.status_code == status.HTTP_201_CREATED, r1.data

    r2 = authenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert r2.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in str(r2.data)


@pytest.mark.django_db
def test_create_variant_rejects_malformed_dvar(authenticated_client, classical_dsvg):
    from django.core.files.uploadedfile import SimpleUploadedFile

    response = authenticated_client.post(
        reverse("variant-list"),
        {
            "dvar": SimpleUploadedFile("bad.json", b"{not json", "application/json"),
            "dsvg": SimpleUploadedFile("a.svg", classical_dsvg.encode(), "image/svg+xml"),
        },
        format="multipart",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_variant_rejects_schema_violation(authenticated_client, classical_dvar, classical_dsvg):
    dvar = copy.deepcopy(classical_dvar)
    dvar["id"] = "missing-nations"
    dvar["nations"] = []
    response = authenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_own_draft_success(authenticated_client, classical_dvar, classical_dsvg):
    dvar = copy.deepcopy(classical_dvar)
    dvar["id"] = "my-draft-2"
    dvar["name"] = "Original Name"
    create_response = authenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    variant_id = create_response.data["id"]

    dvar["name"] = "Updated Name"
    update_response = authenticated_client.put(
        reverse("variant-detail", kwargs={"pk": variant_id}),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert update_response.status_code == status.HTTP_200_OK, update_response.data
    assert update_response.data["name"] == "Updated Name"


@pytest.mark.django_db
def test_update_published_variant_forbidden(authenticated_client, classical_dvar, classical_dsvg):
    response = authenticated_client.put(
        reverse("variant-detail", kwargs={"pk": "classical"}),
        _dvar_upload(classical_dvar, classical_dsvg),
        format="multipart",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_update_other_users_draft_forbidden(
    authenticated_client, authenticated_client_for_secondary_user, classical_dvar, classical_dsvg
):
    dvar = copy.deepcopy(classical_dvar)
    dvar["id"] = "owned-by-secondary"
    create_response = authenticated_client_for_secondary_user.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    variant_id = create_response.data["id"]

    update_response = authenticated_client.put(
        reverse("variant-detail", kwargs={"pk": variant_id}),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert update_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_delete_own_draft_cascades_sandbox_games(
    authenticated_client, primary_user, classical_dvar, classical_dsvg
):
    from game.models import Game

    dvar = copy.deepcopy(classical_dvar)
    dvar["id"] = "to-delete"
    create_response = authenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    variant_id = create_response.data["id"]

    variant = Variant.objects.get(id=variant_id)
    Game.objects.create_sandbox(user=primary_user, name="Test Sandbox", variant=variant)
    assert Game.objects.filter(variant=variant).count() == 1

    delete_response = authenticated_client.delete(
        reverse("variant-detail", kwargs={"pk": variant_id}),
    )
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT
    assert not Variant.objects.filter(id=variant_id).exists()
    assert Game.objects.filter(variant_id=variant_id).count() == 0


@pytest.mark.django_db
def test_delete_published_variant_forbidden(authenticated_client):
    response = authenticated_client.delete(
        reverse("variant-detail", kwargs={"pk": "classical"}),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_download_dvar_system_variant(authenticated_client):
    response = authenticated_client.get(
        reverse("variant-dvar", kwargs={"variant_id": "classical"}),
    )
    assert response.status_code == status.HTTP_200_OK
    assert response["Content-Type"] == "application/json"
    assert "attachment" in response["Content-Disposition"]
    payload = json.loads(response.content)
    assert payload["id"] == "classical"
    assert payload["schemaVersion"] == 1


@pytest.mark.django_db
def test_download_dvar_owned_variant_emits_slug(
    authenticated_client, classical_dvar, classical_dsvg
):
    dvar = copy.deepcopy(classical_dvar)
    dvar["id"] = "my-slug"
    create_response = authenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    variant_id = create_response.data["id"]

    download_response = authenticated_client.get(
        reverse("variant-dvar", kwargs={"variant_id": variant_id}),
    )
    assert download_response.status_code == status.HTTP_200_OK
    payload = json.loads(download_response.content)
    assert payload["id"] == "my-slug"


@pytest.mark.django_db
def test_download_then_reupload_roundtrips(
    authenticated_client, classical_dvar, classical_dsvg
):
    dvar = copy.deepcopy(classical_dvar)
    dvar["id"] = "roundtrip"
    create_response = authenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    variant_id = create_response.data["id"]

    download_response = authenticated_client.get(
        reverse("variant-dvar", kwargs={"variant_id": variant_id}),
    )
    downloaded_dvar = json.loads(download_response.content)

    update_response = authenticated_client.put(
        reverse("variant-detail", kwargs={"pk": variant_id}),
        _dvar_upload(downloaded_dvar, classical_dsvg),
        format="multipart",
    )
    assert update_response.status_code == status.HTTP_200_OK, update_response.data


@pytest.mark.django_db
def test_game_create_rejects_draft_variant(authenticated_client, primary_user, classical_dvar, classical_dsvg):
    dvar = copy.deepcopy(classical_dvar)
    dvar["id"] = "draft-for-game"
    create_response = authenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    variant_id = create_response.data["id"]

    response = authenticated_client.post(
        reverse("game-create"),
        {
            "name": "Game on draft",
            "variant_id": variant_id,
            "nation_assignment": "random",
            "private": False,
            "deadline_mode": "duration",
        },
        format="json",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "variant_id" in response.data


@pytest.mark.django_db
def test_dvar_reupload_preserves_flags_for_surviving_nations(
    authenticated_client, classical_dvar, classical_dsvg
):
    from django.core.files.uploadedfile import SimpleUploadedFile
    from nation.models import NationFlag

    dvar = copy.deepcopy(classical_dvar)
    dvar["id"] = "preserve-flags"
    create_response = authenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    variant_id = create_response.data["id"]

    flag_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>'
    flag_upload = {"flag": SimpleUploadedFile("flag.svg", flag_svg.encode(), "image/svg+xml")}
    assert (
        authenticated_client.put(
            reverse("nation-flag", kwargs={"variant_id": variant_id, "nation_id": "england"}),
            flag_upload,
            format="multipart",
        ).status_code
        == status.HTTP_200_OK
    )
    flag_hash_before = NationFlag.objects.get(
        nation__variant_id=variant_id, nation__nation_id="england"
    ).content_hash

    update_response = authenticated_client.put(
        reverse("variant-detail", kwargs={"pk": variant_id}),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert update_response.status_code == status.HTTP_200_OK, update_response.data

    flag_after = NationFlag.objects.get(
        nation__variant_id=variant_id, nation__nation_id="england"
    )
    assert flag_after.content_hash == flag_hash_before


@pytest.mark.django_db
def test_dvar_reupload_drops_flags_for_removed_nations(
    authenticated_client, classical_dvar, classical_dsvg
):
    from django.core.files.uploadedfile import SimpleUploadedFile
    from nation.models import NationFlag

    dvar = copy.deepcopy(classical_dvar)
    dvar["id"] = "drop-flags"
    create_response = authenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    variant_id = create_response.data["id"]

    flag_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"/>'
    flag_upload = {"flag": SimpleUploadedFile("flag.svg", flag_svg.encode(), "image/svg+xml")}
    assert (
        authenticated_client.put(
            reverse("nation-flag", kwargs={"variant_id": variant_id, "nation_id": "england"}),
            flag_upload,
            format="multipart",
        ).status_code
        == status.HTTP_200_OK
    )

    renamed = copy.deepcopy(dvar)
    for nation in renamed["nations"]:
        if nation["id"] == "england":
            nation["id"] = "britain"
            nation["name"] = "Britain"
    for province in renamed["provinces"]:
        if province.get("homeNation") == "england":
            province["homeNation"] = "britain"
    for unit in renamed["initialState"]["units"]:
        if unit["nation"] == "england":
            unit["nation"] = "britain"
    for sc in renamed["initialState"]["supplyCenters"]:
        if sc["nation"] == "england":
            sc["nation"] = "britain"

    update_response = authenticated_client.put(
        reverse("variant-detail", kwargs={"pk": variant_id}),
        _dvar_upload(renamed, classical_dsvg),
        format="multipart",
    )
    assert update_response.status_code == status.HTTP_200_OK, update_response.data

    assert not NationFlag.objects.filter(
        nation__variant_id=variant_id, nation__nation_id="england"
    ).exists()
    assert not NationFlag.objects.filter(
        nation__variant_id=variant_id, nation__nation_id="britain"
    ).exists()


@pytest.mark.django_db
def test_sandbox_game_accepts_draft_variant(authenticated_client, classical_dvar, classical_dsvg):
    dvar = copy.deepcopy(classical_dvar)
    dvar["id"] = "draft-for-sandbox"
    create_response = authenticated_client.post(
        reverse("variant-list"),
        _dvar_upload(dvar, classical_dsvg),
        format="multipart",
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    variant_id = create_response.data["id"]

    response = authenticated_client.post(
        reverse("sandbox-game-create"),
        {"name": "Sandbox of draft", "variant_id": variant_id},
        format="json",
    )
    assert response.status_code == status.HTTP_201_CREATED, response.data
