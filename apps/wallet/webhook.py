import hashlib
import hmac
import logging

from django.conf import settings
from django.http import HttpRequest

from apps.core.exceptions import APIException


logger = logging.getLogger(__name__)


class PaystackWebhookValidator:
    """Validator for Paystack webhook requests"""

    @staticmethod
    def validate_signature(request: HttpRequest) -> bool:
        """
        Validate Paystack webhook signature

        Args:
            request: Django HttpRequest object

        Returns:
            bool: True if signature is valid
        """
        signature = request.headers.get("x-paystack-signature")

        if not signature:
            logger.warning("Missing Paystack signature in webhook")
            raise APIException("Missing signature", status_code=400)

        # Get request body
        body = request.body

        # Calculate expected signature
        secret = settings.PAYSTACK_SECRET_KEY.encode("utf-8")
        expected_signature = hmac.new(secret, body, hashlib.sha512).hexdigest()
        print(secret)
        print(expected_signature)

        # Compare signatures
        is_valid = hmac.compare_digest(signature, expected_signature)

        if not is_valid:
            logger.warning("Invalid Paystack webhook signature")
            raise APIException("Invalid signature", status_code=400)

        logger.info("Paystack webhook signature validated successfully")
        return True

    @staticmethod
    def is_duplicate_event(event_id: str) -> bool:
        """
        Check if webhook event has already been processed
        This helps ensure idempotency

        For now, we'll use transaction reference as the unique identifier
        You could implement a more sophisticated caching/tracking system
        """
        # TODO: Implement caching or database tracking of processed events
        # For now, we rely on the database unique constraint on reference
        return False
