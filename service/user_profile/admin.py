from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'email')
    search_fields = ('name', 'user__email', 'user__username')
