from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from blog.models import BlogPost


class TestBlogPostListView:

    @pytest.mark.django_db
    def test_anonymous_reader_can_list_posts(
        self, unauthenticated_client, blog_post_factory
    ):
        blog_post_factory("first-post", title="First post", summary="The first one")
        response = unauthenticated_client.get(reverse("blog-post-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["slug"] == "first-post"
        assert response.data[0]["title"] == "First post"
        assert response.data[0]["summary"] == "The first one"
        assert "created_at" in response.data[0]

    @pytest.mark.django_db
    def test_list_omits_body(self, unauthenticated_client, blog_post_factory):
        blog_post_factory("first-post")
        response = unauthenticated_client.get(reverse("blog-post-list"))
        assert "body" not in response.data[0]

    @pytest.mark.django_db
    def test_lists_newest_post_first(self, unauthenticated_client, blog_post_factory):
        older = blog_post_factory("older")
        blog_post_factory("newer")
        BlogPost.objects.filter(pk=older.pk).update(
            created_at=timezone.now() - timedelta(days=1)
        )
        response = unauthenticated_client.get(reverse("blog-post-list"))
        assert [post["slug"] for post in response.data] == ["newer", "older"]

    @pytest.mark.django_db
    def test_authenticated_reader_can_list_posts(
        self, authenticated_client, blog_post_factory
    ):
        blog_post_factory("first-post")
        response = authenticated_client.get(reverse("blog-post-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

    @pytest.mark.django_db
    def test_empty_blog_lists_no_posts(self, unauthenticated_client):
        response = unauthenticated_client.get(reverse("blog-post-list"))
        assert response.status_code == status.HTTP_200_OK
        assert response.data == []


class TestBlogPostRetrieveView:

    @pytest.mark.django_db
    def test_anonymous_reader_can_read_post(
        self, unauthenticated_client, blog_post_factory
    ):
        blog_post_factory(
            "first-post",
            title="First post",
            summary="The first one",
            body="# Hello\n\nWorld",
        )
        response = unauthenticated_client.get(
            reverse("blog-post-detail", args=["first-post"])
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["slug"] == "first-post"
        assert response.data["title"] == "First post"
        assert response.data["summary"] == "The first one"
        assert response.data["body"] == "# Hello\n\nWorld"

    @pytest.mark.django_db
    def test_unknown_slug_returns_not_found(self, unauthenticated_client):
        response = unauthenticated_client.get(
            reverse("blog-post-detail", args=["missing"])
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
