from django.contrib import admin
from .models import Wallet, Transaction


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ["user", "balance", "created_at", "updated_at"]
    search_fields = ["user__email"]
    readonly_fields = ["created_at", "updated_at"]
    list_filter = ["created_at"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "reference",
        "user",
        "transaction_type",
        "amount",
        "status",
        "created_at",
    ]
    search_fields = ["reference", "user__email", "paystack_reference"]
    list_filter = ["transaction_type", "status", "created_at"]
    readonly_fields = ["reference", "created_at", "updated_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("user", "reference", "transaction_type", "amount", "status")},
        ),
        ("Transfer Details", {"fields": ("recipient_wallet_number", "recipient")}),
        (
            "Paystack Details",
            {"fields": ("paystack_reference", "authorization_url", "access_code")},
        ),
        ("Metadata", {"fields": ("metadata",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
    )
