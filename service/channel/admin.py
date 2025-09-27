from django.contrib import admin
from .models import Channel, ChannelMember, ChannelMessage


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ("name", "game", "private", "created_at")
    list_filter = ("private", "game")
    search_fields = ("name",)


@admin.register(ChannelMember)
class ChannelMemberAdmin(admin.ModelAdmin):
    list_display = ("member", "channel", "created_at")
    list_filter = ("channel",)


@admin.register(ChannelMessage)
class ChannelMessageAdmin(admin.ModelAdmin):
    list_display = ("sender", "channel", "created_at")
    list_filter = ("channel",)
    search_fields = ("body",)
