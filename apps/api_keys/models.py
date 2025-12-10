from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class APIKey(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")
    name = models.CharField(max_length=100, help_text="Friendly name for the API key")
    key_hash = models.CharField(max_length=128, unique=True, db_index=True)
    prefix = models.CharField(
        max_length=20,
        db_index=True,
        help_text="First few chars of key for identification",
    )
    permissions = models.JSONField(
        default=list,
        help_text="List of permissions: deposit, transfer, read",
    )
    expires_at = models.DateTimeField(db_index=True)
    is_revoked = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "api_keys"
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_revoked", "expires_at"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.prefix}***) - {self.user.email}"

    def clean(self):
        valid_permissions = {"deposit", "transfer", "read"}
        if self.permissions:
            invalid = set(self.permissions) - valid_permissions
            if invalid:
                raise ValidationError(f"Invalid permissions: {invalid}")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if the key is expired"""
        from django.utils import timezone

        return timezone.now() > self.expires_at

    @property
    def is_active(self):
        """Check if the key is active (not expired and not revoked)"""
        return not self.is_expired and not self.is_revoked

    def revoke(self):
        """Revoke this API key"""
        self.is_revoked = True
        self.save(update_fields=["is_revoked", "updated_at"])

    def update_last_used(self):
        """Update the last used timestamp"""
        from django.utils import timezone

        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at"])
