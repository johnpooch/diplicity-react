from django.contrib import admin
from django.contrib import messages

from .models import UserProfile, UserProfilePicture


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("name",)
    actions = ["clear_uploaded_picture"]

    def clear_uploaded_picture(self, request, queryset):
        pictures = UserProfilePicture.objects.filter(profile__in=queryset).select_related("profile")
        names = sorted(picture.profile.name for picture in pictures)

        if not names:
            self.message_user(
                request, "None of the selected profiles has an uploaded picture.", level=messages.WARNING
            )
            return

        pictures.delete()
        self.message_user(
            request,
            f"Cleared the uploaded picture for {', '.join(names)}.",
            level=messages.SUCCESS,
        )

    clear_uploaded_picture.short_description = "Clear uploaded profile picture"
