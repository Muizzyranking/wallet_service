PAYSTACK_MIN_AMOUNT = 100
PAYSTACK_MAX_AMOUNT = 100_000_000

MIN_DEPOSIT_AMOUNT = PAYSTACK_MIN_AMOUNT
MAX_DEPOSIT_AMOUNT = PAYSTACK_MAX_AMOUNT

MIN_TRANSFER_AMOUNT = 100  # 1 NGN in kobo
MAX_TRANSFER_AMOUNT = 100_000_000  # 1,000,000 NGN in kobo


def validate_deposit_amount(amount: int) -> None:
    """Validate deposit amount is within Paystack limits"""
    if amount < MIN_DEPOSIT_AMOUNT:
        raise ValueError(
            f"Minimum deposit amount is {MIN_DEPOSIT_AMOUNT} kobo ({MIN_DEPOSIT_AMOUNT / 100} NGN)"
        )
    if amount > MAX_DEPOSIT_AMOUNT:
        raise ValueError(
            f"Maximum deposit amount is {MAX_DEPOSIT_AMOUNT} kobo ({MAX_DEPOSIT_AMOUNT / 100} NGN)"
        )


def validate_transfer_amount(amount: int) -> None:
    """Validate transfer amount is within limits"""
    if amount < MIN_TRANSFER_AMOUNT:
        raise ValueError(
            f"Minimum transfer amount is {MIN_TRANSFER_AMOUNT} kobo ({MIN_TRANSFER_AMOUNT / 100} NGN)"
        )
    if amount > MAX_TRANSFER_AMOUNT:
        raise ValueError(
            f"Maximum transfer amount is {MAX_TRANSFER_AMOUNT} kobo ({MAX_TRANSFER_AMOUNT / 100} NGN)"
        )


def kobo_to_naira(kobo: int) -> float:
    """Convert kobo to naira"""
    return kobo / 100


def naira_to_kobo(naira: float) -> int:
    """Convert naira to kobo"""
    return int(naira * 100)
