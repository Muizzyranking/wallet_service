from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "wallet_number", "google_id", "created_at"]
    search_fields = ["user__email", "wallet_number", "google_id"]
    list_filter = ["created_at"]
    readonly_fields = ["wallet_number", "created_at", "updated_at"]

    fieldsets = (
        ("User Information", {"fields": ("user", "google_id", "profile_picture")}),
        ("Wallet Information", {"fields": ("wallet_number",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
