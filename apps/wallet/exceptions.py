class WalletException(Exception):
    """Base exception for wallet operations"""

    pass


class InsufficientBalanceException(WalletException):
    """Raised when wallet has insufficient balance"""

    pass


class WalletNotFoundException(WalletException):
    """Raised when wallet is not found"""

    pass


class InvalidAmountException(WalletException):
    """Raised when amount is invalid"""

    pass


class DuplicateTransactionException(WalletException):
    """Raised when transaction reference already exists"""

    pass


class PaystackException(Exception):
    """Base exception for Paystack operations"""

    pass


class PaystackAPIException(PaystackException):
    """Raised when Paystack API returns an error"""

    pass


class PaystackWebhookException(PaystackException):
    """Raised when webhook validation fails"""

    pass
