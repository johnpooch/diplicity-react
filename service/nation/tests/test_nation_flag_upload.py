import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from nation.models import NationFlag


def _flag_upload(svg, filename="flag.svg"):
    return {"flag": SimpleUploadedFile(filename, svg.encode(), "image/svg+xml")}


@pytest.mark.django_db
def test_upload_requires_authentication(unauthenticated_client, draft_variant_for_primary, minimal_flag_svg):
    response = unauthenticated_client.put(
        reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}),
        _flag_upload(minimal_flag_svg),
        format="multipart",
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_upload_to_published_variant_forbidden(
    authenticated_client, classical_variant, classical_england_nation, minimal_flag_svg
):
    response = authenticated_client.put(
        reverse(
            "nation-flag",
            kwargs={"variant_id": "classical", "nation_id": classical_england_nation.nation_id},
        ),
        _flag_upload(minimal_flag_svg),
        format="multipart",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_upload_to_other_users_draft_forbidden(
    authenticated_client, draft_variant_for_secondary, minimal_flag_svg
):
    response = authenticated_client.put(
        reverse("nation-flag", kwargs={"variant_id": "secondary-draft", "nation_id": "greens"}),
        _flag_upload(minimal_flag_svg),
        format="multipart",
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_upload_own_draft_flag_success(
    authenticated_client, draft_variant_for_primary, minimal_flag_svg
):
    response = authenticated_client.put(
        reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}),
        _flag_upload(minimal_flag_svg),
        format="multipart",
    )
    assert response.status_code == status.HTTP_200_OK, response.data
    assert response.data["nation_id"] == "reds"
    assert response.data["flag_url"] is not None
    assert NationFlag.objects.filter(
        nation__variant_id="primary-draft", nation__nation_id="reds"
    ).exists()


@pytest.mark.django_db
def test_upload_replaces_existing_flag(
    authenticated_client, draft_variant_for_primary, minimal_flag_svg
):
    url = reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"})
    first = authenticated_client.put(url, _flag_upload(minimal_flag_svg), format="multipart")
    second_svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 5 5"/>'
    second = authenticated_client.put(url, _flag_upload(second_svg), format="multipart")
    assert first.status_code == second.status_code == status.HTTP_200_OK
    assert first.data["flag_url"] != second.data["flag_url"]
    assert (
        NationFlag.objects.filter(
            nation__variant_id="primary-draft", nation__nation_id="reds"
        ).count()
        == 1
    )


@pytest.mark.django_db
def test_upload_rejects_oversize(authenticated_client, draft_variant_for_primary):
    huge = '<svg xmlns="http://www.w3.org/2000/svg">' + ("<rect/>" * 50000) + "</svg>"
    response = authenticated_client.put(
        reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}),
        _flag_upload(huge),
        format="multipart",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_upload_rejects_malformed_svg(authenticated_client, draft_variant_for_primary):
    response = authenticated_client.put(
        reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}),
        _flag_upload("<svg><rect"),
        format="multipart",
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_upload_sanitizes_scripts(authenticated_client, draft_variant_for_primary):
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<script>alert(1)</script><rect id="r1" onclick="x"/>'
        "</svg>"
    )
    response = authenticated_client.put(
        reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"}),
        _flag_upload(svg),
        format="multipart",
    )
    assert response.status_code == status.HTTP_200_OK
    flag = NationFlag.objects.get(
        nation__variant_id="primary-draft", nation__nation_id="reds"
    )
    assert "<script" not in flag.svg
    assert "onclick" not in flag.svg


@pytest.mark.django_db
def test_delete_flag(authenticated_client, draft_variant_for_primary, minimal_flag_svg):
    url = reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "reds"})
    authenticated_client.put(url, _flag_upload(minimal_flag_svg), format="multipart")
    response = authenticated_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not NationFlag.objects.filter(
        nation__variant_id="primary-draft", nation__nation_id="reds"
    ).exists()


@pytest.mark.django_db
def test_unknown_nation_returns_404(
    authenticated_client, draft_variant_for_primary, minimal_flag_svg
):
    response = authenticated_client.put(
        reverse("nation-flag", kwargs={"variant_id": "primary-draft", "nation_id": "nonexistent"}),
        _flag_upload(minimal_flag_svg),
        format="multipart",
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
