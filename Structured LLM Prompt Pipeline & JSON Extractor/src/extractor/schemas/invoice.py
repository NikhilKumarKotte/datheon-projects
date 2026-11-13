from typing import List, Literal, Optional
from pydantic import Field
from src.extractor.schemas.base import StrictModel


class InvoiceLineItem(StrictModel):
    """Individual line item or service billed on an invoice."""
    description: str = Field(description="Description of the purchased item or service")
    quantity: Optional[float] = Field(default=None, description="Quantity, or null if not stated")
    unit_price: Optional[float] = Field(default=None, description="Price per unit, or null if not stated")
    line_total: Optional[float] = Field(default=None, description="Line total, or null if not stated")


class InvoiceData(StrictModel):
    """Comprehensive structured invoice representation."""
    invoice_number: Optional[str] = Field(default=None, description="Invoice identifier")
    seller: Optional[str] = Field(default=None, description="Seller or supplier name")
    customer: Optional[str] = Field(default=None, description="Customer or buyer name")
    invoice_date: Optional[str] = Field(default=None, description="Date in YYYY-MM-DD format, or null if unknown")
    due_date: Optional[str] = Field(default=None, description="Payment due date in YYYY-MM-DD format, or null if unknown")
    total_amount: Optional[float] = Field(default=None, description="Final invoice total as a number")
    currency: Optional[str] = Field(default=None, description="Currency code such as INR, USD, or EUR")
    payment_status: Literal["paid", "unpaid", "partially_paid", "unknown"] = Field(
        default="unknown",
        description="Payment status explicitly stated by the document",
    )
    line_items: List[InvoiceLineItem] = Field(
        default_factory=list,
        description="Items listed on the invoice; empty list if none are stated",
    )
