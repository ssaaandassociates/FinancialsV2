"""
Rounding Utility
Handles conversion of absolute Rupee amounts to Hundreds/Thousands/Lakhs
and tracks rounding differences for BS and PL adjustment.

BS rounding difference → Other Current Assets / Other Current Liabilities
PL rounding difference → Miscellaneous Expenses
"""

DIVISORS = {
    "Rupees": 1,
    "Hundreds": 100,
    "Thousands": 1000,
    "Lakhs": 100000,
}

LABELS = {
    "Rupees": "(Amount in Indian Rupees)",
    "Hundreds": "(Amount in Hundreds)",
    "Thousands": "(Amount in Thousands)",
    "Lakhs": "(Amount in Lakhs)",
}


def round_amount(amount: float, rounding: str = "Rupees") -> float:
    """Round a single amount to the specified denomination."""
    divisor = DIVISORS.get(rounding, 1)
    if divisor == 1:
        return round(amount, 2)
    return round(amount / divisor, 2)


def compute_rounding_difference(amounts: list[float], rounding: str = "Rupees") -> dict:
    """
    Compute the rounding difference for a list of amounts.
    Returns: {total_original, total_rounded, difference}
    """
    divisor = DIVISORS.get(rounding, 1)
    if divisor == 1:
        return {"total_original": sum(amounts), "total_rounded": sum(amounts), "difference": 0}

    total_original = sum(amounts) / divisor
    total_rounded = sum(round(a / divisor, 2) for a in amounts)
    difference = round(total_original - total_rounded, 2)

    return {
        "total_original": round(total_original, 2),
        "total_rounded": total_rounded,
        "difference": difference,
    }


def get_rounding_label(rounding: str) -> str:
    """Get the display label for the rounding denomination."""
    return LABELS.get(rounding, "(Amount in Indian Rupees)")
