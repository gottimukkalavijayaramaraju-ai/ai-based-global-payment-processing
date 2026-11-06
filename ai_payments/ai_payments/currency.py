"""Simple multi-currency support.
Rates are static demo values (units of currency per 1 USD).
In production, fetch them from a live FX provider and cache them.
"""
RATES_PER_USD = {
    "USD": 1.0, "EUR": 0.92, "GBP": 0.79, "INR": 83.0, "JPY": 150.0,
    "AUD": 1.52, "CAD": 1.36, "SGD": 1.34, "AED": 3.67, "BRL": 5.0,
}


def to_usd(amount: float, currency: str) -> float:
    currency = currency.upper()
    if currency not in RATES_PER_USD:
        raise ValueError(f"Unsupported currency: {currency}")
    return round(amount / RATES_PER_USD[currency], 2)


def convert(amount: float, src: str, dst: str) -> float:
    return round(to_usd(amount, src) * RATES_PER_USD[dst.upper()], 2)
