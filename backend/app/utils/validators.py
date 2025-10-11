import re
from datetime import date
from typing import Any

from fastapi import HTTPException, status

from ..models import Account, AccountType, Category, User

# Constants
MAX_TRANSACTION_AMOUNT = 1_000_000
MAX_IMPORT_FILE_SIZE_MB = 5
MAX_PAGE_SIZE = 100
MAX_DATE_RANGE_DAYS = 365
MIN_PHONE_DIGITS = 10
MAX_PHONE_DIGITS = 15
EMAIL_PATTERN = r'^[\w\.-]+@[\w\.-]+ \.\w+$'
PHONE_PATTERN = r'^\d{10,15}$'


class ValidationError(HTTPException):
    """Custom validation error"""
    def __init__(self, detail: str):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

class Validators:
    @staticmethod
    def validate_account_ownership(db: Any, account_id: int, user_id: int) -> Account:
        """Validate that user owns the account (primary or joint owner)"""
        # First check if user is primary owner
        account = db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == user_id,
            Account.is_active
        ).first()

        if account:
            return account

        # Check if user is joint owner
        user = db.query(User).get(user_id)
        if user and hasattr(user, 'joint_accounts') and user.joint_accounts:
            for joint_account in user.joint_accounts:
                if joint_account.id == account_id and joint_account.is_active:
                    return joint_account

        raise ValidationError("Account not found or access denied")

    @staticmethod
    def validate_category_access(db: Any, category_id: int, user_id: int) -> Category:
        """Validate user has access to category (system or own)"""
        from ..storage.memory_adapter import ORClause

        category = db.query(Category).filter(
            Category.id == category_id,
            ORClause(Category.is_system == True, Category.user_id == user_id)
        ).first()

        if not category:
            raise ValidationError("Category not found or access denied")

        return category

    @staticmethod
    def validate_transfer_accounts(db: Any, from_account_id: int, to_account_id: int, user_id: int):
        """Validate accounts for transfer"""
        if from_account_id == to_account_id:
            raise ValidationError("Cannot transfer to the same account")

        from_account = Validators.validate_account_ownership(db, from_account_id, user_id)
        to_account = Validators.validate_account_ownership(db, to_account_id, user_id)

        return from_account, to_account

    @staticmethod
    def validate_transaction_amount(amount: float, account_type: AccountType | None = None):
        """Validate transaction amount"""
        if amount <= 0:
            raise ValidationError("Amount must be greater than 0")

        if amount > MAX_TRANSACTION_AMOUNT:
            raise ValidationError("Amount exceeds maximum allowed")

    @staticmethod
    def validate_budget_period(start_date: date, end_date: date | None = None):
        """Validate budget period dates"""
        if end_date and end_date <= start_date:
            raise ValidationError("End date must be after start date")

        if start_date < date.today().replace(day=1):
            raise ValidationError("Start date cannot be in the past")

    @staticmethod
    def validate_goal_amount(current_amount: float, target_amount: float):
        """Validate goal amounts"""
        if target_amount <= 0:
            raise ValidationError("Target amount must be greater than 0")

        if current_amount < 0:
            raise ValidationError("Current amount cannot be negative")

        if current_amount > target_amount:
            raise ValidationError("Current amount cannot exceed target amount")

    @staticmethod
    def validate_credit_limit(account: Account, new_balance: float):
        """Validate credit card limit"""
        if account.account_type == AccountType.CREDIT_CARD and account.credit_limit and new_balance < -account.credit_limit:
            raise ValidationError(f"Transaction would exceed credit limit of ${account.credit_limit}")

    @staticmethod
    def validate_sufficient_funds(account: Account, amount: float):
        """Validate sufficient funds for debit"""
        if account.account_type in [AccountType.CHECKING, AccountType.SAVINGS] and account.balance < amount:
            raise ValidationError(f"Insufficient funds. Available balance: ${account.balance:.2f}")

    @staticmethod
    def validate_date_range(start_date: date | None, end_date: date | None):
        """Validate date range for queries"""
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError("End date must be after start date")

            # Limit range to 1 year
            if (end_date - start_date).days > MAX_DATE_RANGE_DAYS:
                raise ValidationError("Date range cannot exceed 1 year")

    @staticmethod
    def validate_contact_request(db: Any, user_id: int, contact_id: int):
        """Validate contact request"""
        if user_id == contact_id:
            raise ValidationError("Cannot add yourself as a contact")

        # Check if contact exists
        contact_user = db.query(User).filter(User.id == contact_id).first()
        if not contact_user:
            raise ValidationError("User not found")

        return contact_user

    @staticmethod
    def validate_csv_file(file_content: str, filename: str):
        """Validate CSV file for import"""
        if not filename.lower().endswith('.csv'):
            raise ValidationError("File must be a CSV")

        # Check file size (base64 encoded)
        if len(file_content) > MAX_IMPORT_FILE_SIZE_MB * 1024 * 1024 * 1.37:  # Base64 overhead
            raise ValidationError(f"File size exceeds {MAX_IMPORT_FILE_SIZE_MB}MB limit")

    @staticmethod
    def validate_pagination(page: int = 1, page_size: int = 20):
        """Validate pagination parameters"""
        if page < 1:
            raise ValidationError("Page must be greater than 0")

        if page_size < 1 or page_size > MAX_PAGE_SIZE:
            raise ValidationError("Page size must be between 1 and 100")

        return page, page_size


# Utility functions for common validations
def validate_email(email: str) -> bool:
    """Basic email validation"""
    return re.match(EMAIL_PATTERN, email) is not None


def validate_phone(phone: str) -> bool:
    """Basic phone validation"""
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    # Check if it's a valid number (10-15 digits)
    return re.match(PHONE_PATTERN, cleaned) is not None

def sanitize_string(value: str, max_length: int = 255) -> str:
    """Sanitize string input"""
    if value:
        # Remove leading/trailing whitespace
        value = value.strip()
        # Limit length
        value = value[:max_length]
    return value
