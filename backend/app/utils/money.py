"""
Utility functions for handling monetary values.
Ensures all money values are properly formatted with exactly 2 decimal places.
"""
from decimal import ROUND_HALF_UP, Decimal


def format_money(amount: float | int | str | Decimal | None) -> float:
    """
    Format a monetary amount to exactly 2 decimal places.
    
    Args:
        amount: The amount to format (can be float, int, string, Decimal, or None)
        
    Returns:
        float: The amount rounded to 2 decimal places
    """
    if amount is None:
        return 0.0

    # Convert to Decimal for precise rounding
    try:
        decimal_amount = Decimal(str(amount))
        # Round to 2 decimal places using banker's rounding
        rounded = decimal_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return float(rounded)
    except (ValueError, TypeError):
        return 0.0


def safe_add_money(amount1: float | int | None, amount2: float | int | None) -> float:
    """
    Safely add two monetary amounts and return result with 2 decimal places.
    
    Args:
        amount1: First amount
        amount2: Second amount
        
    Returns:
        float: Sum rounded to 2 decimal places
    """
    val1 = format_money(amount1)
    val2 = format_money(amount2)
    return format_money(val1 + val2)


def safe_subtract_money(amount1: float | int | None, amount2: float | int | None) -> float:
    """
    Safely subtract two monetary amounts and return result with 2 decimal places.
    
    Args:
        amount1: Amount to subtract from
        amount2: Amount to subtract
        
    Returns:
        float: Difference rounded to 2 decimal places
    """
    val1 = format_money(amount1)
    val2 = format_money(amount2)
    return format_money(val1 - val2)


def safe_multiply_money(amount: float | int | None, factor: float | int | None) -> float:
    """
    Safely multiply a monetary amount by a factor and return result with 2 decimal places.
    
    Args:
        amount: The monetary amount
        factor: The multiplication factor
        
    Returns:
        float: Product rounded to 2 decimal places
    """
    val = format_money(amount)
    mult = float(factor) if factor is not None else 0.0
    return format_money(val * mult)


def validate_positive_amount(amount: float | int | None, field_name: str = "amount") -> float:
    """
    Validate that an amount is positive and properly formatted.
    
    Args:
        amount: The amount to validate
        field_name: Name of the field for error messages
        
    Returns:
        float: The validated and formatted amount
        
    Raises:
        ValueError: If amount is negative or invalid
    """
    formatted_amount = format_money(amount)
    if formatted_amount < 0:
        raise ValueError(f"{field_name} must be positive")
    return formatted_amount
