from django.contrib import admin
from .models import RetainedCommitment, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(RetainedCommitment)
class RetainedCommitmentAdmin(admin.ModelAdmin):
    list_display = ("email_hash", "commitment", "created_at")
