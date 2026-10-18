import pytest

from blog.models import BlogPost


@pytest.fixture
def blog_post_factory(db):
    def _create(slug, title="Title", summary="Summary", body="Body"):
        return BlogPost.objects.create(slug=slug, title=title, summary=summary, body=body)

    return _create
