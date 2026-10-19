from rest_framework import generics
from rest_framework.permissions import AllowAny

from blog.models import BlogPost
from blog.serializers import BlogPostListSerializer, BlogPostRetrieveSerializer


class BlogPostListView(generics.ListAPIView):
    """
    Lists every blog post, newest first. The body is omitted; fetch a post by
    slug to read it.
    """

    permission_classes = [AllowAny]
    serializer_class = BlogPostListSerializer
    queryset = BlogPost.objects.all()


class BlogPostRetrieveView(generics.RetrieveAPIView):
    """
    Returns a single blog post by slug, including its Markdown body.
    """

    permission_classes = [AllowAny]
    serializer_class = BlogPostRetrieveSerializer
    queryset = BlogPost.objects.all()
    lookup_field = "slug"
