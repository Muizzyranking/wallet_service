import httpx
from django.conf import settings
from typing import Dict, Optional
import logging
from .exceptions import PaystackAPIException

logger = logging.getLogger(__name__)


class PaystackService:
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.base_url = "https://api.paystack.co"
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    async def initialize_transaction(
        self,
        email: str,
        amount: int,
        reference: str,
        callback_url: Optional[str] = None,
    ) -> Dict:
        """
        Initialize a Paystack transaction

        Args:
            email: Customer email
            amount: Amount in kobo (multiply naira by 100)
            reference: Unique transaction reference
            callback_url: Optional callback URL after payment

        Returns:
            Dict with authorization_url, access_code, and reference
        """
        url = f"{self.base_url}/transaction/initialize"

        payload = {
            "email": email,
            "amount": amount,
            "reference": reference,
        }

        if callback_url:
            payload["callback_url"] = callback_url

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self.headers)
                response.raise_for_status()

                data = response.json()

                if not data.get("status"):
                    raise PaystackAPIException(f"Paystack error: {data.get('message')}")

                logger.info(f"Paystack transaction initialized: {reference}")
                return data["data"]

        except httpx.HTTPError as e:
            logger.error(f"Paystack API error: {str(e)}")
            raise PaystackAPIException(f"Failed to initialize transaction: {str(e)}")

    async def verify_transaction(self, reference: str) -> Dict:
        """
        Verify a Paystack transaction

        Args:
            reference: Transaction reference

        Returns:
            Dict with transaction details
        """
        url = f"{self.base_url}/transaction/verify/{reference}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers)
                response.raise_for_status()

                data = response.json()

                if not data.get("status"):
                    raise PaystackAPIException(f"Paystack error: {data.get('message')}")

                logger.info(f"Paystack transaction verified: {reference}")
                return data["data"]

        except httpx.HTTPError as e:
            logger.error(f"Paystack verification error: {str(e)}")
            raise PaystackAPIException(f"Failed to verify transaction: {str(e)}")

    @staticmethod
    def convert_to_kobo(amount: float) -> int:
        """Convert naira amount to kobo (smallest currency unit)"""
        return int(amount * 100)

    @staticmethod
    def convert_from_kobo(amount: int) -> float:
        """Convert kobo to naira"""
        return amount / 100
