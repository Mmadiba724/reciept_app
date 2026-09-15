"""Convert an integer amount (in minor units / cents) to words for receipts.

Example: amount_cents=150000000, currency="UGX" -> "One Million Five Hundred
Thousand Shillings Only" (UGX has no minor-unit denomination in practice, so
cents are treated as whole-unit amounts times 100 the same as other currencies
here — see CURRENCY_UNITS below for the words used per currency).
"""

ONES = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen",
]
TENS = [
    "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety",
]
SCALES = [(1_000_000_000, "Billion"), (1_000_000, "Million"), (1_000, "Thousand")]

CURRENCY_UNITS: dict[str, tuple[str, str]] = {
    "UGX": ("Shillings", "Cents"),
    "KES": ("Shillings", "Cents"),
    "TZS": ("Shillings", "Cents"),
    "USD": ("Dollars", "Cents"),
    "GBP": ("Pounds", "Pence"),
    "EUR": ("Euros", "Cents"),
    "NGN": ("Naira", "Kobo"),
}


def _three_digit_words(n: int) -> str:
    parts = []
    if n >= 100:
        parts.append(f"{ONES[n // 100]} Hundred")
        n %= 100
    if n >= 20:
        tens_word = TENS[n // 10]
        if n % 10:
            tens_word += f"-{ONES[n % 10]}"
        parts.append(tens_word)
    elif n > 0:
        parts.append(ONES[n])
    return " ".join(parts)


def integer_to_words(n: int) -> str:
    if n == 0:
        return "Zero"
    parts = []
    remainder = n
    for scale_value, scale_name in SCALES:
        if remainder >= scale_value:
            count, remainder = divmod(remainder, scale_value)
            parts.append(f"{_three_digit_words(count)} {scale_name}")
    if remainder > 0:
        parts.append(_three_digit_words(remainder))
    return " ".join(parts)


def amount_to_words(amount_cents: int, currency: str) -> str:
    """`amount_cents` is the amount in minor units (e.g. cents). Whole major
    units and any remaining minor units are both spelled out."""
    if amount_cents < 0:
        raise ValueError("amount_cents must not be negative")

    major_unit, minor_unit = CURRENCY_UNITS.get(currency.upper(), (currency.upper(), "Cents"))
    major, minor = divmod(amount_cents, 100)

    words = f"{integer_to_words(major)} {major_unit}"
    if minor:
        words += f" and {integer_to_words(minor)} {minor_unit}"
    return f"{words} Only"
