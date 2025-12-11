from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.conf import settings


class TransactionType(models.TextChoices):
    DEPOSIT = "deposit", "Deposit"
    TRANSFER = "transfer", "Transfer"


class TransactionStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    SUCCESS = "success", "Success"
    FAILED = "failed", "Failed"


class Wallet(models.Model):
    """Wallet model for storing user balances"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet"
    )
    balance = models.BigIntegerField(default=0, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "wallets"
        verbose_name = "Wallet"
        verbose_name_plural = "Wallets"

    def __str__(self):
        return f"{self.user.email} - Balance: {self.balance}"

    def credit(self, amount: Decimal) -> None:
        """Credit the wallet"""
        self.balance += amount
        self.save(update_fields=["balance", "updated_at"])

    def debit(self, amount: Decimal) -> None:
        """Debit the wallet (raises exception if insufficient balance)"""
        if self.balance < amount:
            raise ValueError("Insufficient balance")
        self.balance -= amount
        self.save(update_fields=["balance", "updated_at"])


class Transaction(models.Model):
    """Transaction model for tracking all wallet activities"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions"
    )

    reference = models.CharField(max_length=100, unique=True, db_index=True)

    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)

    amount = models.BigIntegerField()
    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
    )

    recipient_wallet_number = models.CharField(max_length=13, null=True, blank=True)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="received_transactions",
    )

    paystack_reference = models.CharField(
        max_length=100, null=True, blank=True, unique=True
    )
    authorization_url = models.URLField(null=True, blank=True)
    access_code = models.CharField(max_length=100, null=True, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transactions"
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status", "created_at"]),
            models.Index(fields=["reference"]),
            models.Index(fields=["paystack_reference"]),
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} - {self.status} - {self.user.email}"

    def mark_success(self):
        """Mark transaction as successful"""
        self.status = TransactionStatus.SUCCESS
        self.save(update_fields=["status", "updated_at"])

    def mark_failed(self):
        """Mark transaction as failed"""
        self.status = TransactionStatus.FAILED
        self.save(update_fields=["status", "updated_at"])
