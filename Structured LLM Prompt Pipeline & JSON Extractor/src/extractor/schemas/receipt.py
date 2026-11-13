from typing import List, Literal, Optional
from pydantic import Field
from src.extractor.schemas.base import StrictModel


class ReceiptLineItem(StrictModel):
    """Individual purchased item on a receipt or expense slip."""
    description: str = Field(description="Name or description of the purchased item")
    quantity: Optional[float] = Field(default=None, description="Quantity purchased, or null if unstated")
    price: Optional[float] = Field(default=None, description="Total price for this line item as a number")
    category: Optional[str] = Field(default=None, description="Item category (e.g., food, beverage, electronics, supplies)")


class ReceiptData(StrictModel):
    """Structured representation of a retail receipt, restaurant bill, or expense voucher."""
    merchant_name: Optional[str] = Field(default=None, description="Name of the merchant, vendor, or store")
    merchant_address: Optional[str] = Field(default=None, description="Physical address or location of the merchant")
    merchant_phone: Optional[str] = Field(default=None, description="Merchant phone number if present")
    transaction_date: Optional[str] = Field(default=None, description="Date of purchase in YYYY-MM-DD format")
    transaction_time: Optional[str] = Field(default=None, description="Time of purchase in HH:MM format, or null")
    receipt_number: Optional[str] = Field(default=None, description="Receipt number, transaction number, or order ID")
    subtotal_amount: Optional[float] = Field(default=None, description="Subtotal before taxes and tips")
    tax_amount: Optional[float] = Field(default=None, description="Total sales tax, VAT, or GST amount")
    tip_amount: Optional[float] = Field(default=None, description="Tip or gratuity amount, or null if unstated")
    total_amount: Optional[float] = Field(default=None, description="Final total amount charged or paid")
    currency: Optional[str] = Field(default=None, description="Currency code (e.g. USD, EUR, INR, GBP)")
    payment_method: Literal[
        "cash",
        "credit_card",
        "debit_card",
        "mobile_payment",
        "other",
        "unknown"
    ] = Field(
        default="unknown",
        description="Method used for payment (cash, credit_card, debit_card, mobile_payment, other, unknown)",
    )
    card_last_four: Optional[str] = Field(default=None, description="Last 4 digits of payment card if present")
    expense_category: Literal[
        "meals_and_entertainment",
        "travel",
        "office_supplies",
        "lodging",
        "transportation",
        "utilities",
        "retail",
        "other"
    ] = Field(
        default="retail",
        description="General business expense category",
    )
    line_items: List[ReceiptLineItem] = Field(
        default_factory=list,
        description="List of purchased items on the receipt",
    )
