from django.contrib import admin
from .models import APIKey


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "user",
        "prefix",
        "permissions",
        "expires_at",
        "is_revoked",
        "is_active",
        "created_at",
    ]
    list_filter = ["is_revoked", "created_at", "expires_at"]
    search_fields = ["name", "user__email", "prefix"]
    readonly_fields = ["key_hash", "prefix", "created_at", "updated_at", "last_used_at"]

    fieldsets = (
        ("Basic Information", {"fields": ("user", "name", "prefix")}),
        (
            "Security",
            {"fields": ("key_hash", "permissions", "expires_at", "is_revoked")},
        ),
        ("Timestamps", {"fields": ("created_at", "updated_at", "last_used_at")}),
    )

    def is_active(self, obj):
        return obj.is_active

    is_active.boolean = True
    is_active.short_description = "Active"
