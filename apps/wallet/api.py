import json
import logging

from apps.core.auth import jwt_or_api_key_auth
from django.http import HttpRequest
from django.views.decorators.csrf import csrf_exempt
from ninja import Router
from ninja.responses import Response

from apps.api_keys.permissions import PermissionValidator

from .schemas import (
    BalanceSchema,
    DepositResponseSchema,
    DepositSchema,
    DepositStatusSchema,
    ErrorSchema,
    TransactionListSchema,
    TransferResponseSchema,
    TransferSchema,
)
from .services import WalletService
from .webhook import PaystackWebhookValidator

logger = logging.getLogger(__name__)

router = Router(tags=["Wallet"])


def check_api_key_permission(request: HttpRequest, permission: str):
    """Helper to check API key permissions"""
    if hasattr(request, "auth_type") and request.auth_type == "api_key":
        if not PermissionValidator.validate_permission(request.api_key, permission):
            return Response(
                {"detail": f"API key does not have '{permission}' permission"},
                status=403,
            )
    return None


@router.post(
    "/deposit",
    response={200: DepositResponseSchema, 400: ErrorSchema, 403: ErrorSchema},
    auth=jwt_or_api_key_auth,
    summary="Initiate Deposit",
)
async def deposit(request: HttpRequest, payload: DepositSchema):
    """
    Initiate a deposit using Paystack

    - Requires JWT or API key with 'deposit' permission
    - Returns Paystack payment link
    - User completes payment on Paystack
    - Webhook updates balance after successful payment
    """
    perm_check = check_api_key_permission(request, "deposit")
    if perm_check:
        return perm_check

    transaction, authorization_url = await WalletService.initiate_deposit(
        user=request.auth, amount=payload.amount
    )

    return {
        "reference": transaction.reference,
        "authorization_url": authorization_url,
        "amount": transaction.amount,
    }


@router.post(
    "/paystack/webhook",
    response={200: dict},
    auth=None,  # No auth for webhooks
    summary="Paystack Webhook",
)
@csrf_exempt
async def paystack_webhook(request: HttpRequest):
    """
    Handle Paystack webhook events

    - Validates webhook signature
    - Credits wallet on successful payment
    - Idempotent (won't credit twice)
    """
    try:
        # Validate signature
        PaystackWebhookValidator.validate_signature(request)

        # Parse webhook data
        body = json.loads(request.body)
        event = body.get("event")
        data = body.get("data", {})

        logger.info(f"Paystack webhook received: {event}")

        # Handle charge success event
        if event == "charge.success":
            reference = data.get("reference")
            status = data.get("status")

            if status == "success" and reference:
                # Process deposit (sync operation with transaction.atomic)
                from asgiref.sync import sync_to_async

                await sync_to_async(WalletService.process_successful_deposit)(reference)
                logger.info(f"Webhook processed successfully: {reference}")

        return {"status": True}

    except Exception as e:
        logger.error(f"Webhook error: {str(e)}", exc_info=True)
        return Response({"status": False, "error": str(e)}, status=400)


@router.get(
    "/deposit/{reference}/status",
    response={200: DepositStatusSchema, 400: ErrorSchema},
    auth=jwt_or_api_key_auth,
    summary="Check Deposit Status",
)
async def deposit_status(request: HttpRequest, reference: str):
    """
    Check deposit transaction status

    - Does NOT credit wallet (only webhook does that)
    - Use for manual status checks
    """
    try:
        transaction = await WalletService.get_transaction_by_reference(reference)

        # Verify it belongs to the user
        if transaction.user.id != request.auth.id:
            return Response({"detail": "Transaction not found"}, status=400)

        return {
            "reference": transaction.reference,
            "status": transaction.status,
            "amount": transaction.amount,
        }

    except Exception as e:
        logger.error(f"Status check error: {str(e)}")
        return Response({"detail": "Transaction not found"}, status=400)


@router.get(
    "/balance",
    response={200: BalanceSchema, 400: ErrorSchema, 403: ErrorSchema},
    auth=jwt_or_api_key_auth,
    summary="Get Wallet Balance",
)
async def get_balance(request: HttpRequest):
    """
    Get wallet balance

    - Requires JWT or API key with 'read' permission
    """
    # Check API key permission
    perm_check = check_api_key_permission(request, "read")
    if perm_check:
        return perm_check

    try:
        balance = await WalletService.get_balance(request.auth)
        return {"balance": balance}

    except Exception as e:
        logger.error(f"Balance fetch error: {str(e)}")
        return Response({"detail": "Failed to fetch balance"}, status=400)


@router.post(
    "/transfer",
    response={200: TransferResponseSchema, 400: ErrorSchema, 403: ErrorSchema},
    auth=jwt_or_api_key_auth,
    summary="Transfer Funds",
)
async def transfer(request: HttpRequest, payload: TransferSchema):
    """
    Transfer funds to another wallet

    - Requires JWT or API key with 'transfer' permission
    - Atomic operation (all or nothing)
    - Checks for sufficient balance
    """
    # Check API key permission
    perm_check = check_api_key_permission(request, "transfer")
    if perm_check:
        return perm_check

    transaction = await WalletService.transfer_funds(
        sender=request.auth,
        recipient_wallet_number=payload.wallet_number,
        amount=payload.amount,
    )

    return {
        "status": "success",
        "message": "Transfer completed",
        "reference": transaction.reference,
        "amount": transaction.amount,
    }


@router.get(
    "/transactions",
    response={200: TransactionListSchema, 403: ErrorSchema},
    auth=jwt_or_api_key_auth,
    summary="Get Transaction History",
)
async def get_transactions(request: HttpRequest):
    """
    Get transaction history

    - Requires JWT or API key with 'read' permission
    - Returns last 50 transactions
    """
    # Check API key permission
    perm_check = check_api_key_permission(request, "read")
    if perm_check:
        return perm_check

    try:
        transactions = await WalletService.get_transaction_history(request.auth)

        return {
            "transactions": [
                {
                    "id": txn.id,
                    "transaction_type": txn.transaction_type,
                    "amount": txn.amount,
                    "status": txn.status,
                    "reference": txn.reference,
                    "recipient_wallet_number": txn.recipient_wallet_number,
                    "created_at": txn.created_at,
                }
                for txn in transactions
            ],
            "count": len(transactions),
        }
    except Exception as e:
        logger.error(f"Transaction history error: {str(e)}")
        return Response({"detail": "Failed to fetch transactions"}, status=400)
