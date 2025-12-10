import logging
import uuid
from decimal import Decimal
from typing import List, Optional, Tuple

from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.db import transaction

from apps.authentication.models import UserProfile

from .exceptions import (
    DuplicateTransactionException,
    InsufficientBalanceException,
    InvalidAmountException,
    WalletNotFoundException,
)
from .models import Transaction, Wallet
from .paystack import PaystackService

logger = logging.getLogger(__name__)


class WalletService:
    """Service for wallet operations"""

    @staticmethod
    @sync_to_async
    def get_or_create_wallet(user: User) -> Wallet:
        """Get or create wallet for a user"""
        wallet, created = Wallet.objects.get_or_create(user=user)
        if created:
            logger.info(f"Wallet created for user: {user.email}")
        return wallet

    @staticmethod
    @sync_to_async
    def get_balance(user: User) -> Decimal:
        """Get wallet balance"""
        try:
            wallet = Wallet.objects.get(user=user)
            return wallet.balance
        except Wallet.DoesNotExist:
            raise WalletNotFoundException("Wallet not found")

    @staticmethod
    def generate_transaction_reference() -> str:
        """Generate unique transaction reference"""
        return f"TXN-{uuid.uuid4().hex[:16].upper()}"

    @staticmethod
    async def initiate_deposit(
        user: User, amount: int
    ) -> Tuple[Transaction, Optional[str]]:
        """
        Initiate a deposit transaction with Paystack

        Returns: (Transaction, authorization_url)
        """
        if amount <= 0:
            raise InvalidAmountException("Amount must be greater than 0")

        await WalletService.get_or_create_wallet(user)

        reference = WalletService.generate_transaction_reference()

        paystack = PaystackService()

        try:
            paystack_response = await paystack.initialize_transaction(
                email=user.email, amount=amount, reference=reference
            )
        except Exception as e:
            logger.error(f"Failed to initialize Paystack transaction: {str(e)}")
            raise

        transaction_obj = await sync_to_async(Transaction.objects.create)(
            user=user,
            reference=reference,
            transaction_type="deposit",
            amount=amount,
            status="pending",
            paystack_reference=paystack_response.get("reference"),
            authorization_url=paystack_response.get("authorization_url"),
            access_code=paystack_response.get("access_code"),
        )

        logger.info(f"Deposit initiated for {user.email}: {amount}")

        return transaction_obj, paystack_response.get("authorization_url")

    @staticmethod
    @transaction.atomic
    def process_successful_deposit(reference: str) -> Transaction:
        """
        Process a successful deposit (called by webhook)
        This is idempotent - won't credit twice for same reference
        """
        try:
            txn = Transaction.objects.select_for_update().get(
                reference=reference, transaction_type="deposit"
            )
        except Transaction.DoesNotExist:
            raise DuplicateTransactionException(f"Transaction not found: {reference}")

        if txn.status == "success":
            logger.warning(f"Transaction already processed: {reference}")
            return txn

        wallet = Wallet.objects.select_for_update().get(user=txn.user)
        wallet.credit(txn.amount)

        txn.mark_success()

        logger.info(f"Deposit successful for {txn.user.email}: {txn.amount}")

        return txn

    @staticmethod
    @sync_to_async
    @transaction.atomic
    def transfer_funds(
        sender: User, recipient_wallet_number: str, amount: int
    ) -> Transaction:
        """
        Transfer funds from one wallet to another
        This is atomic - either both succeed or both fail
        """
        if amount <= 0:
            raise InvalidAmountException("Amount must be greater than 0")

        # Get sender wallet
        try:
            sender_wallet = Wallet.objects.select_for_update().get(user=sender)
        except Wallet.DoesNotExist:
            raise WalletNotFoundException("Sender wallet not found")

        # Check balance
        if sender_wallet.balance < amount:
            raise InsufficientBalanceException("Insufficient balance")

        # Find recipient by wallet number
        try:
            recipient_profile = UserProfile.objects.select_related("user").get(
                wallet_number=recipient_wallet_number
            )
            recipient = recipient_profile.user
        except UserProfile.DoesNotExist:
            raise WalletNotFoundException("Recipient wallet not found")

        # Can't transfer to self
        if sender.id == recipient.id:
            raise InvalidAmountException("Cannot transfer to yourself")

        # Get recipient wallet
        recipient_wallet, _ = Wallet.objects.select_for_update().get_or_create(
            user=recipient
        )

        # Generate reference
        reference = WalletService.generate_transaction_reference()

        # Debit sender
        sender_wallet.debit(amount)

        # Credit recipient
        recipient_wallet.credit(amount)

        # Create transaction record for sender
        txn = Transaction.objects.create(
            user=sender,
            reference=reference,
            transaction_type="transfer",
            amount=amount,
            status="success",
            recipient_wallet_number=recipient_wallet_number,
            recipient=recipient,
        )

        # Create transaction record for recipient
        Transaction.objects.create(
            user=recipient,
            reference=f"{reference}-RECV",
            transaction_type="transfer",
            amount=amount,
            status="success",
            recipient_wallet_number=sender.profile.wallet_number,
            recipient=sender,
            metadata={"sender": sender.email},
        )

        logger.info(
            f"Transfer successful: {sender.email} -> {recipient.email}: {amount}"
        )

        return txn

    @staticmethod
    @sync_to_async
    def get_transaction_history(user: User) -> List[Transaction]:
        """Get transaction history for a user"""
        return list(Transaction.objects.filter(user=user).order_by("-created_at")[:50])

    @staticmethod
    @sync_to_async
    def get_transaction_by_reference(reference: str) -> Transaction:
        """Get transaction by reference"""
        try:
            txn = Transaction.objects.get(reference=reference)
            print(txn)
            return txn
        except Transaction.DoesNotExist:
            raise DuplicateTransactionException(f"Transaction not found: {reference}")
