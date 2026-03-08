# =====================================================
# CASH SERVICE
# Handles cash breakdown, totals, expected cash, and diff
# =====================================================

from constants import CASH_DENOMINATIONS


# =====================================================
# Helpers
# =====================================================
def safe_float(value) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def safe_int(value) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


# =====================================================
# Breakdown Builders
# =====================================================
def build_cash_breakdown_from_quantities(quantities: dict) -> dict:
    """
    Expects:
    {
        "200": 1,
        "100": 2,
        "50": 0,
        ...
        "coins": 3.5
    }
    """
    breakdown = {}
    total = 0.0

    for denomination in CASH_DENOMINATIONS:
        key = str(denomination)
        qty = safe_int(quantities.get(key, 0))
        subtotal = qty * denomination

        breakdown[key] = {
            "qty": qty,
            "total": subtotal,
        }
        total += subtotal

    coins = safe_float(quantities.get("coins", 0))
    breakdown["coins"] = {
        "qty": coins,
        "total": coins,
    }
    total += coins

    breakdown["_meta"] = {"grand_total": total}
    return breakdown


def calculate_breakdown_total(breakdown: dict) -> float:
    if not breakdown:
        return 0.0

    if "_meta" in breakdown:
        return safe_float(breakdown["_meta"].get("grand_total", 0))

    total = 0.0
    for key, value in breakdown.items():
        if key == "_meta":
            continue
        total += safe_float(value.get("total", 0))
    return total


def normalize_breakdown(breakdown: dict) -> dict:
    """
    Ensures the breakdown is always in the same shape.
    """
    breakdown = breakdown or {}
    normalized_input = {}

    for denomination in CASH_DENOMINATIONS:
        key = str(denomination)
        item = breakdown.get(key, {})
        normalized_input[key] = item.get("qty", 0)

    coins_item = breakdown.get("coins", {})
    normalized_input["coins"] = coins_item.get("qty", 0)

    return build_cash_breakdown_from_quantities(normalized_input)


# =====================================================
# Formatting
# =====================================================
def format_cash_breakdown_text(breakdown: dict) -> str:
    breakdown = normalize_breakdown(breakdown)

    lines = []
    for denomination in CASH_DENOMINATIONS:
        key = str(denomination)
        qty = breakdown[key]["qty"]
        total = safe_float(breakdown[key]["total"])
        lines.append(f"• {denomination} LE: {qty} = {total:,.2f}")

    coins_qty = breakdown["coins"]["qty"]
    coins_total = safe_float(breakdown["coins"]["total"])
    lines.append(f"• Coins: {coins_qty} = {coins_total:,.2f}")

    return "\n".join(lines)


# =====================================================
# Calculations
# =====================================================
def calculate_total_expenses(expenses: list) -> float:
    return sum(safe_float(item.get("amount", 0)) for item in (expenses or []))


def calculate_total_digital(instapay=0, wallet=0, visa=0) -> float:
    return safe_float(instapay) + safe_float(wallet) + safe_float(visa)


def calculate_expected_cash(
    opening_cash: float,
    sales: float,
    total_expenses: float,
    total_digital: float,
) -> float:
    return (
        safe_float(opening_cash)
        + safe_float(sales)
        - safe_float(total_expenses)
        - safe_float(total_digital)
    )


def calculate_cash_difference(actual_cash: float, expected_cash: float) -> float:
    return safe_float(actual_cash) - safe_float(expected_cash)


# =====================================================
# Unified Summary
# =====================================================
def build_cash_summary(
    opening_breakdown: dict,
    closing_breakdown: dict,
    sales: float,
    expenses: list,
    instapay: float = 0,
    wallet: float = 0,
    visa: float = 0,
) -> dict:
    opening_breakdown = normalize_breakdown(opening_breakdown)
    closing_breakdown = normalize_breakdown(closing_breakdown)

    opening_total = calculate_breakdown_total(opening_breakdown)
    closing_total = calculate_breakdown_total(closing_breakdown)
    total_expenses = calculate_total_expenses(expenses)
    total_digital = calculate_total_digital(instapay, wallet, visa)
    expected_cash = calculate_expected_cash(
        opening_cash=opening_total,
        sales=sales,
        total_expenses=total_expenses,
        total_digital=total_digital,
    )
    difference = calculate_cash_difference(
        actual_cash=closing_total,
        expected_cash=expected_cash,
    )

    return {
        "opening_breakdown": opening_breakdown,
        "closing_breakdown": closing_breakdown,
        "opening_total": opening_total,
        "closing_total": closing_total,
        "opening_text": format_cash_breakdown_text(opening_breakdown),
        "closing_text": format_cash_breakdown_text(closing_breakdown),
        "total_expenses": total_expenses,
        "total_digital": total_digital,
        "expected_cash": expected_cash,
        "difference": difference,
    }
