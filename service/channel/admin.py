from django.contrib import admin
from .models import Channel, ChannelMember, ChannelMessage


@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        Channel.objects.save_channel(obj)

    def delete_model(self, request, obj):
        Channel.objects.delete_channels(Channel.objects.filter(pk=obj.pk))

    def delete_queryset(self, request, queryset):
        Channel.objects.delete_channels(queryset)

    list_display = ("name", "game", "private", "created_at")
    list_filter = ("private", "game")
    search_fields = ("name",)


@admin.register(ChannelMember)
class ChannelMemberAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        ChannelMember.objects.save_membership(obj)

    def delete_model(self, request, obj):
        ChannelMember.objects.delete_memberships(
            ChannelMember.objects.filter(pk=obj.pk)
        )

    def delete_queryset(self, request, queryset):
        ChannelMember.objects.delete_memberships(queryset)

    list_display = ("member", "channel", "created_at")
    list_filter = ("channel",)


@admin.register(ChannelMessage)
class ChannelMessageAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        ChannelMessage.objects.save_message(obj)

    def delete_model(self, request, obj):
        ChannelMessage.objects.filter(pk=obj.pk).delete_messages()

    def delete_queryset(self, request, queryset):
        queryset.delete_messages()

    list_display = ("sender", "channel", "created_at")
    list_filter = ("channel",)
    search_fields = ("body",)
