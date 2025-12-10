import uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    wallet_number = models.CharField(max_length=13, unique=True, db_index=True)
    profile_picture = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profiles"
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"

    def __str__(self):
        return f"{self.user.email} - {self.wallet_number}"

    @staticmethod
    def generate_wallet_number():
        while True:
            wallet_number = "".join([str(uuid.uuid4().int)[:13]])
            if (
                len(wallet_number) == 13
                and not UserProfile.objects.filter(wallet_number=wallet_number).exists()
            ):
                return wallet_number

    def save(self, *args, **kwargs):
        if not self.wallet_number:
            self.wallet_number = self.generate_wallet_number()
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    """Auto-create wallet and profile when user is created"""
    if created:
        from apps.wallet.models import Wallet

        UserProfile.objects.get_or_create(user=instance)
        Wallet.objects.get_or_create(user=instance)
