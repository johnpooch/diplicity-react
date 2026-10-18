from django.contrib import admin

from blog.models import BlogPost


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "created_at", "updated_at"]
    search_fields = ["title", "slug"]
    prepopulated_fields = {"slug": ["title"]}
