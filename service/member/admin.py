from django.contrib import admin
from .models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'game', 'nation', 'won', 'drew', 'eliminated', 'kicked')
    list_filter = ('won', 'drew', 'eliminated', 'kicked')
    search_fields = ('user__username', 'game__name')
    raw_id_fields = ('user', 'game', 'nation')