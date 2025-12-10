from ninja import Schema
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class DepositSchema(Schema):
    amount: int

    class Config:
        json_schema_extra = {"example": {"amount": 5000}}


class DepositResponseSchema(Schema):
    """Schema for deposit response"""

    reference: str
    authorization_url: str
    amount: int


class DepositStatusSchema(Schema):
    """Schema for deposit status response"""

    reference: str
    status: str  # success, failed, pending
    amount: Decimal


class TransferSchema(Schema):
    """Schema for transfer request"""

    wallet_number: str
    amount: Decimal

    class Config:
        json_schema_extra = {
            "example": {"wallet_number": "1234567890123", "amount": 3000}
        }


class TransferResponseSchema(Schema):
    """Schema for transfer response"""

    status: str
    message: str
    reference: str
    amount: Decimal


class BalanceSchema(Schema):
    """Schema for wallet balance"""

    balance: Decimal


class TransactionSchema(Schema):
    """Schema for transaction history"""

    id: int
    transaction_type: str
    amount: Decimal
    status: str
    reference: str
    recipient_wallet_number: Optional[str] = None
    created_at: datetime


class TransactionListSchema(Schema):
    """Schema for transaction list response"""

    transactions: List[TransactionSchema]
    count: int


class MessageSchema(Schema):
    """Generic message response"""

    message: str


class ErrorSchema(Schema):
    """Error response schema"""

    detail: str
