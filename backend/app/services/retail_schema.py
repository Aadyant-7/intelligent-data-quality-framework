"""Conservative, explainable matching of common retail column names.

Matching is based on normalized whole names and documented aliases, never on
substring guesses. Ambiguous roles are deliberately left unresolved.
"""

import re
from collections.abc import Iterable


ROLE_ALIASES = {
    "transaction_id": ("InvoiceNo", "Invoice ID", "Invoice Number", "Transaction ID", "Transaction No", "Order ID", "Order Number"),
    "quantity": ("Quantity", "Qty", "Units Sold", "Units Purchased"),
    "unit_price": ("UnitPrice", "Unit Price", "Price Per Unit", "Price/Unit", "Price Each", "Item Price"),
    "product_id": ("StockCode", "Stock Code", "SKU", "Product ID", "Product Code", "Item Code"),
    "product_name": ("Description", "Product Description", "Product Name", "Item Description"),
    "line_total": ("Total Spent", "Line Total", "Line Amount", "Sales Amount", "Subtotal", "Total"),
    "tax_amount": ("Tax 5%", "Tax Amount", "Sales Tax", "Tax Charged"),
    "discount_applied": ("Discount Applied", "Is Discounted"),
}


def _normalize(name: str) -> str:
    spaced = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", name)
    return re.sub(r"[^a-z0-9]", "", spaced.lower())


def resolve_retail_schema(columns: Iterable[str]) -> dict[str, object]:
    """Return matched fields and ambiguous candidates for transparent checks."""
    names = list(columns)
    matches: dict[str, str] = {}
    ambiguous: dict[str, list[str]] = {}
    for role, aliases in ROLE_ALIASES.items():
        accepted = {_normalize(alias) for alias in aliases}
        candidates = [name for name in names if _normalize(name) in accepted]
        if len(candidates) == 1:
            matches[role] = candidates[0]
        elif len(candidates) > 1:
            ambiguous[role] = candidates
    return {"matches": matches, "ambiguous": ambiguous}
