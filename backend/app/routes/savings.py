import math
from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ..models import (
    Account,
    Any,
    ChallengeJoinRequest,
    ChallengeParticipant,
    ChallengeStatus,
    ChallengeType,
    Goal,
    GoalContribution,
    GoalStatus,
    RoundUpConfig,
    RoundUpConfigRequest,
    RoundUpConfigResponse,
    RoundUpStatus,
    RoundUpTransaction,
    RoundUpTransactionResponse,
    SavingsChallenge,
    SavingsChallengeResponse,
    SavingsGoalCreate,
    SavingsRule,
    SavingsRuleFrequency,
    SavingsRuleRequest,
    SavingsRuleResponse,
    SavingsRuleType,
    Transaction,
    TransactionStatus,
    TransactionType,
    User,
)
from ..storage.memory_adapter import db
from ..utils.auth import get_current_user
from ..utils.validators import ValidationError

router = APIRouter()

# Savings Goals CRUD endpoints

@router.post("", response_model=dict, status_code=status.HTTP_200_OK)
async def create_savings_goal(
    request: Request,
    goal_data: SavingsGoalCreate,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create a new savings goal"""

    # Verify account ownership if account specified
    if goal_data.account_id:
        account = db_session.query(Account).filter(
            Account.id == goal_data.account_id,
            Account.user_id == current_user['user_id']
        ).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )

    # Rename fields to match database model
    goal_dict = goal_data.dict()

    # Handle both 'goal_name' and 'name' field names
    if 'goal_name' in goal_dict:
        goal_dict['name'] = goal_dict.pop('goal_name')

    # Handle 'category' field from request
    category = None
    if 'category' in goal_dict:
        category = goal_dict.pop('category')
        # Map category string to category_id
        category_map = {
            'emergency': 16,  # Savings category
            'vacation': 17,   # Travel category
            'home': 18,       # Home category
            'vehicle': 19,    # Vehicle category
            'other': 20       # Other category
        }
        goal_dict['category_id'] = category_map.get(category, 20)

    # Convert target_date string to date object if present
    if goal_dict.get('target_date'):
        try:
            goal_dict['target_date'] = datetime.fromisoformat(goal_dict['target_date'].replace('Z', '+00:00')).date()
        except:
            goal_dict['target_date'] = datetime.strptime(goal_dict['target_date'], '%Y-%m-%d').date()
    else:
        # Default to 1 year from now if not provided
        goal_dict['target_date'] = (datetime.utcnow() + timedelta(days=365)).date()

    # Create goal
    goal = Goal(
        user_id=current_user['user_id'],
        **{k: v for k, v in goal_dict.items() if k in [
            'name', 'description', 'target_amount', 'current_amount',
            'target_date', 'account_id', 'category_id', 'auto_transfer_enabled',
            'auto_transfer_amount', 'auto_transfer_frequency'
        ]}
    )

    db_session.add(goal)
    db_session.commit()
    db_session.refresh(goal)

    # Prepare response with additional fields
    response_dict = {
        "id": goal.id,
        "user_id": goal.user_id,
        "goal_name": goal.name,  # Map back for compatibility
        "name": goal.name,
        "description": goal.description,
        "target_amount": goal.target_amount,
        "current_amount": goal.current_amount or 0.0,
        "target_date": goal.target_date,
        "status": goal.status,
        "account_id": goal.account_id,
        "category": category or 'other',
        "auto_transfer_enabled": goal.auto_transfer_enabled or False,
        "auto_transfer_amount": goal.auto_transfer_amount,
        "auto_transfer_frequency": goal.auto_transfer_frequency,
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
        "progress_percentage": (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
    }

    return response_dict

@router.get("/summary", response_model=dict)
async def get_savings_summary(
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get savings summary"""
    goals = db_session.query(Goal).filter(
        Goal.user_id == current_user['user_id']
    ).all()

    total_goals = len(goals)
    active_goals = sum(1 for g in goals if g.status == GoalStatus.ACTIVE)
    completed_goals = sum(1 for g in goals if g.status == GoalStatus.COMPLETED)
    total_saved = sum(g.current_amount or 0 for g in goals)
    average_progress = sum((g.current_amount / g.target_amount * 100) if g.target_amount > 0 else 0 for g in goals) / total_goals if total_goals > 0 else 0

    # Group by category
    goals_by_category = {}
    category_names = {
        16: 'emergency',
        17: 'vacation',
        18: 'home',
        19: 'vehicle',
        20: 'other'
    }

    for goal in goals:
        category = category_names.get(goal.category_id, 'other')
        if category not in goals_by_category:
            goals_by_category[category] = {
                'count': 0,
                'total_saved': 0,
                'total_target': 0
            }
        goals_by_category[category]['count'] += 1
        goals_by_category[category]['total_saved'] += goal.current_amount or 0
        goals_by_category[category]['total_target'] += goal.target_amount

    response = {
        "total_saved": total_saved,
        "total_goals": total_goals,
        "active_goals": active_goals,
        "completed_goals": completed_goals,
        "average_progress": average_progress,
        "goals_by_category": goals_by_category
    }

    return response

@router.get("/{goal_id}", response_model=dict)
async def get_savings_goal(
    goal_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get a specific savings goal"""
    goal = db_session.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user['user_id']
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )

    # Calculate additional fields
    days_remaining = None
    monthly_contribution_needed = None

    if goal.target_date:
        days_remaining = (goal.target_date - date.today()).days
        if days_remaining > 0 and goal.target_amount > goal.current_amount:
            remaining_amount = goal.target_amount - goal.current_amount
            months_remaining = days_remaining / 30.0
            monthly_contribution_needed = remaining_amount / months_remaining if months_remaining > 0 else 0

    response = {
        "id": goal.id,
        "user_id": goal.user_id,
        "goal_name": goal.name,
        "name": goal.name,
        "description": goal.description,
        "target_amount": goal.target_amount,
        "current_amount": goal.current_amount or 0.0,
        "target_date": goal.target_date,
        "status": goal.status,
        "account_id": goal.account_id,
        "auto_transfer_enabled": goal.auto_transfer_enabled or False,
        "auto_transfer_amount": goal.auto_transfer_amount,
        "auto_transfer_frequency": goal.auto_transfer_frequency,
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
        "progress_percentage": (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0,
        "days_remaining": days_remaining,
        "monthly_contribution_needed": monthly_contribution_needed
    }

    return response

@router.put("/{goal_id}", response_model=dict)
async def update_savings_goal(
    goal_id: int,
    goal_update: dict,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Update a savings goal"""
    goal = db_session.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user['user_id']
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )

    # Update fields
    update_data = goal_update.copy()
    if 'goal_name' in update_data:
        update_data['name'] = update_data.pop('goal_name')

    # Convert target_date if present
    if update_data.get('target_date'):
        try:
            update_data['target_date'] = datetime.fromisoformat(update_data['target_date'].replace('Z', '+00:00')).date()
        except:
            update_data['target_date'] = datetime.strptime(update_data['target_date'], '%Y-%m-%d').date()

    for field, value in update_data.items():
        if hasattr(goal, field):
            setattr(goal, field, value)

    db_session.commit()
    db_session.refresh(goal)

    response = {
        "id": goal.id,
        "user_id": goal.user_id,
        "goal_name": goal.name,
        "name": goal.name,
        "description": goal.description,
        "target_amount": goal.target_amount,
        "current_amount": goal.current_amount or 0.0,
        "target_date": goal.target_date,
        "status": goal.status,
        "account_id": goal.account_id,
        "auto_transfer_enabled": goal.auto_transfer_enabled or False,
        "auto_transfer_amount": goal.auto_transfer_amount,
        "auto_transfer_frequency": goal.auto_transfer_frequency,
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
        "progress_percentage": (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
    }

    return response

@router.post("/{goal_id}/contribute", response_model=dict)
async def contribute_to_goal(
    request: Request,
    goal_id: int,
    contribution: dict,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Add contribution to a savings goal"""

    goal = db_session.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user['user_id']
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )

    amount = contribution.get('amount', 0)
    from_account_id = contribution.get('from_account_id')
    notes = contribution.get('notes', '')

    if amount <= 0:
        raise ValidationError("Contribution amount must be positive")

    # Verify account ownership
    if from_account_id:
        account = db_session.query(Account).filter(
            Account.id == from_account_id,
            Account.user_id == current_user['user_id']
        ).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )

        # Check sufficient balance
        if account.balance < amount:
            raise ValidationError("Insufficient balance")

        # Update account balance
        account.balance -= amount

    # Update goal amount
    goal.current_amount = (goal.current_amount or 0) + amount
    new_progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
    goal_completed = goal.current_amount >= goal.target_amount

    if goal_completed and goal.status == GoalStatus.ACTIVE:
        goal.status = GoalStatus.COMPLETED
        goal.completed_at = datetime.utcnow()

    # Create contribution record
    contribution_record = GoalContribution(
        goal_id=goal_id,
        amount=amount,
        contribution_date=datetime.utcnow(),
        notes=notes or f"Contribution to {goal.name}"
    )

    # Create transaction record
    if from_account_id:
        transaction = Transaction(
            account_id=from_account_id,
            amount=amount,  # Store as positive with DEBIT type
            transaction_type=TransactionType.DEBIT,
            status=TransactionStatus.COMPLETED,
            description=f"Contribution to goal: {goal.name}",
            transaction_date=datetime.utcnow(),
            category_id=16  # Savings category
        )
        db_session.add(transaction)
        db_session.flush()
        transaction_id = transaction.id
    else:
        transaction_id = None

    db_session.add(contribution_record)
    db_session.commit()

    response = {
        "contribution_amount": amount,
        "new_balance": goal.current_amount,
        "new_progress_percentage": new_progress,
        "goal_completed": goal_completed,
        "transaction_id": transaction_id
    }

    return response

@router.post("/{goal_id}/withdraw", response_model=dict)
async def withdraw_from_goal(
    request: Request,
    goal_id: int,
    withdrawal: dict,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Withdraw from a savings goal"""

    goal = db_session.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user['user_id']
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )

    amount = withdrawal.get('amount', 0)
    to_account_id = withdrawal.get('to_account_id')
    reason = withdrawal.get('reason', '')

    if amount <= 0:
        raise ValidationError("Withdrawal amount must be positive")

    if goal.current_amount < amount:
        raise ValidationError("Insufficient balance in goal")

    # Verify account ownership
    if to_account_id:
        account = db_session.query(Account).filter(
            Account.id == to_account_id,
            Account.user_id == current_user['user_id']
        ).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )

        # Update account balance
        account.balance += amount

    # Update goal amount
    goal.current_amount -= amount
    new_progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0

    # Create transaction record
    if to_account_id:
        transaction = Transaction(
            account_id=to_account_id,
            amount=amount,
            transaction_type=TransactionType.CREDIT,
            status=TransactionStatus.COMPLETED,
            description=f"Withdrawal from goal: {goal.name}",
            transaction_date=datetime.utcnow(),
            category_id=16  # Savings category
        )
        db_session.add(transaction)

    db_session.commit()

    response = {
        "withdrawal_amount": amount,
        "new_balance": goal.current_amount,
        "new_progress_percentage": new_progress
    }

    return response

@router.delete("/{goal_id}", status_code=status.HTTP_200_OK)
async def delete_savings_goal(
    request: Request,
    goal_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Delete a savings goal"""

    goal = db_session.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user['user_id']
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )

    goal_name = goal.name
    db_session.delete(goal)
    db_session.commit()

    return {"message": f"Goal '{goal_name}' deleted successfully"}

@router.get("", response_model=list[dict])
async def list_savings_goals(
    category: str | None = None,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """List all savings goals with optional filtering"""
    query = db_session.query(Goal).filter(
        Goal.user_id == current_user['user_id']
    )

    if category:
        # Map category string to category_id
        category_map = {
            'emergency': 16,
            'vacation': 17,
            'home': 18,
            'vehicle': 19,
            'other': 20
        }
        if category in category_map:
            query = query.filter(Goal.category_id == category_map[category])

    goals = query.order_by(Goal.created_at.desc()).all()

    response = []
    for goal in goals:
        goal_dict = {
            "id": goal.id,
            "user_id": goal.user_id,
            "goal_name": goal.name,
            "name": goal.name,
            "description": goal.description,
            "target_amount": goal.target_amount,
            "current_amount": goal.current_amount or 0.0,
            "target_date": goal.target_date,
            "status": goal.status,
            "account_id": goal.account_id,
            "category": category or 'other',
            "auto_transfer_enabled": goal.auto_transfer_enabled or False,
            "auto_transfer_amount": goal.auto_transfer_amount,
            "auto_transfer_frequency": goal.auto_transfer_frequency,
            "created_at": goal.created_at,
            "updated_at": goal.updated_at,
            "progress_percentage": (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0,
            "is_active": goal.status == GoalStatus.ACTIVE
        }
        response.append(goal_dict)

    return response

@router.get("/{goal_id}/history", response_model=list[dict])
async def get_goal_history(
    goal_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get contribution history for a goal"""
    goal = db_session.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user['user_id']
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )

    # Get contributions from GoalContribution table
    contributions = db_session.query(GoalContribution).filter(
        GoalContribution.goal_id == goal_id
    ).order_by(GoalContribution.contribution_date.desc()).all()

    # Get transactions related to this goal (for withdrawals)
    transactions = db_session.query(Transaction).filter(
        Transaction.description.like(f"%goal: {goal.name}%"),
        Transaction.transaction_type == TransactionType.CREDIT
    ).order_by(Transaction.transaction_date.desc()).all()

    history = []

    # Combine contributions and withdrawals
    for contrib in contributions:
        history.append({
            "amount": contrib.amount,
            "type": "contribution",
            "date": contrib.contribution_date,
            "balance_after": None,  # Will calculate later
            "description": contrib.notes or f"Contribution to {goal.name}"
        })

    for tx in transactions:
        history.append({
            "amount": tx.amount,
            "type": "withdrawal",
            "date": tx.transaction_date,
            "balance_after": None,
            "description": tx.description
        })

    # Sort by date and calculate running balance
    history.sort(key=lambda x: x["date"])
    running_balance = 0

    for entry in history:
        if entry["type"] == "contribution":
            running_balance += entry["amount"]
        else:
            running_balance -= entry["amount"]
        entry["balance_after"] = running_balance

    # Return in reverse chronological order
    return list(reversed(history))

@router.get("/{goal_id}/projections", response_model=dict)
async def get_goal_projections(
    goal_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get goal projections"""
    goal = db_session.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user['user_id']
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )

    remaining_amount = goal.target_amount - (goal.current_amount or 0)

    # Calculate contributions needed
    monthly_needed = 0
    weekly_needed = 0
    projected_date = None
    on_track = True

    if goal.target_date and remaining_amount > 0:
        days_remaining = (goal.target_date - date.today()).days
        if days_remaining > 0:
            monthly_needed = remaining_amount / (days_remaining / 30.0)
            weekly_needed = remaining_amount / (days_remaining / 7.0)
        else:
            on_track = False

    # Calculate projected completion based on auto-transfer
    if goal.auto_transfer_enabled and goal.auto_transfer_amount:
        if goal.auto_transfer_frequency == 'monthly':
            months_needed = remaining_amount / goal.auto_transfer_amount
            projected_date = date.today() + timedelta(days=months_needed * 30)
        elif goal.auto_transfer_frequency == 'weekly':
            weeks_needed = remaining_amount / goal.auto_transfer_amount
            projected_date = date.today() + timedelta(weeks=weeks_needed)
        elif goal.auto_transfer_frequency == 'daily':
            days_needed = remaining_amount / goal.auto_transfer_amount
            projected_date = date.today() + timedelta(days=days_needed)

    # Generate scenarios
    scenarios = [
        {
            "name": "Conservative",
            "monthly_contribution": monthly_needed * 0.8,
            "completion_date": date.today() + timedelta(days=(remaining_amount / (monthly_needed * 0.8) * 30)) if monthly_needed > 0 else None
        },
        {
            "name": "Target",
            "monthly_contribution": monthly_needed,
            "completion_date": goal.target_date
        },
        {
            "name": "Aggressive",
            "monthly_contribution": monthly_needed * 1.2,
            "completion_date": date.today() + timedelta(days=(remaining_amount / (monthly_needed * 1.2) * 30)) if monthly_needed > 0 else None
        }
    ]

    response = {
        "monthly_contribution_needed": monthly_needed,
        "weekly_contribution_needed": weekly_needed,
        "projected_completion_date": projected_date,
        "on_track": on_track,
        "scenarios": scenarios
    }

    return response

@router.put("/{goal_id}/auto-transfer", response_model=dict)
async def configure_auto_transfer(
    request: Request,
    goal_id: int,
    config: dict,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Configure automated transfer for a goal"""

    goal = db_session.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user['user_id']
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )

    # Verify account ownership
    from_account_id = config.get('from_account_id')
    if from_account_id:
        account = db_session.query(Account).filter(
            Account.id == from_account_id,
            Account.user_id == current_user['user_id']
        ).first()
        if not account:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account not found"
            )
        goal.account_id = from_account_id

    # Update auto-transfer settings
    goal.auto_transfer_enabled = config.get('enabled', False)
    goal.auto_transfer_amount = config.get('amount')
    goal.auto_transfer_frequency = config.get('frequency')

    db_session.commit()
    db_session.refresh(goal)

    response = {
        "id": goal.id,
        "goal_name": goal.name,
        "auto_transfer_enabled": goal.auto_transfer_enabled,
        "auto_transfer_amount": goal.auto_transfer_amount,
        "auto_transfer_frequency": goal.auto_transfer_frequency,
        "account_id": goal.account_id
    }

    return response

@router.get("/{goal_id}/milestones", response_model=list[dict])
async def get_goal_milestones(
    goal_id: int,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get milestones for a savings goal"""
    goal = db_session.query(Goal).filter(
        Goal.id == goal_id,
        Goal.user_id == current_user['user_id']
    ).first()

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )

    current_progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0

    milestones = [
        {
            "percentage": 10,
            "amount": goal.target_amount * 0.1,
            "reached": current_progress >= 10,
            "reached_date": None  # Could track this with contribution history
        },
        {
            "percentage": 25,
            "amount": goal.target_amount * 0.25,
            "reached": current_progress >= 25,
            "reached_date": None
        },
        {
            "percentage": 50,
            "amount": goal.target_amount * 0.5,
            "reached": current_progress >= 50,
            "reached_date": None
        },
        {
            "percentage": 75,
            "amount": goal.target_amount * 0.75,
            "reached": current_progress >= 75,
            "reached_date": None
        },
        {
            "percentage": 100,
            "amount": goal.target_amount,
            "reached": current_progress >= 100,
            "reached_date": goal.completed_at if goal.status == GoalStatus.COMPLETED else None
        }
    ]

    return milestones

@router.post("/shared", response_model=dict)
async def create_shared_goal(
    request: Request,
    goal_data: dict,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create a shared savings goal"""

    # Extract shared user
    shared_username = goal_data.pop('shared_with_username', None)
    if not shared_username:
        raise ValidationError("Shared username is required")

    # Find the other user
    shared_user = db_session.query(User).filter(
        User.username == shared_username
    ).first()

    if not shared_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Create goal for current user
    goal_dict = goal_data.copy()
    goal_dict['name'] = goal_dict.pop('goal_name', goal_data.get('name', 'Shared Goal'))

    # Add default target_date if not provided
    if 'target_date' not in goal_dict or not goal_dict['target_date']:
        goal_dict['target_date'] = (datetime.utcnow() + timedelta(days=365)).date()
    # Convert string to date if needed
    elif isinstance(goal_dict['target_date'], str):
        try:
            goal_dict['target_date'] = datetime.fromisoformat(goal_dict['target_date'].replace('Z', '+00:00')).date()
        except:
            goal_dict['target_date'] = datetime.strptime(goal_dict['target_date'], '%Y-%m-%d').date()

    # Extract fields for Goal creation
    goal_fields = {k: v for k, v in goal_dict.items() if k in [
        'name', 'description', 'target_amount', 'current_amount',
        'target_date', 'account_id', 'category_id'
    ]}

    goal1 = Goal(
        user_id=current_user['user_id'],
        **goal_fields
    )

    # Create goal for shared user
    goal2 = Goal(
        user_id=shared_user.id,
        **goal_fields
    )

    db_session.add(goal1)
    db_session.add(goal2)
    db_session.commit()
    db_session.refresh(goal1)

    response = {
        "id": goal1.id,
        "user_id": goal1.user_id,
        "goal_name": goal1.name,
        "name": goal1.name,
        "description": goal1.description,
        "target_amount": goal1.target_amount,
        "current_amount": goal1.current_amount or 0.0,
        "target_date": goal1.target_date,
        "status": goal1.status,
        "category": goal_dict.get('category', 'other'),
        "created_at": goal1.created_at,
        "is_shared": True,
        "participants": [
            {"id": current_user['user_id'], "username": current_user.get('username', 'You')},
            {"id": shared_user.id, "username": shared_user.username}
        ],
        "progress_percentage": (goal1.current_amount / goal1.target_amount * 100) if goal1.target_amount > 0 else 0
    }

    return response

# Existing round-up and rules endpoints below

def calculate_round_up(amount: float, multiplier: float = 1.0) -> float:
    """Calculate round-up amount"""
    # Round up to nearest dollar
    rounded = math.ceil(amount)
    base_round_up = rounded - amount

    # Apply multiplier
    return round(base_round_up * multiplier, 2)

def execute_round_up_transfer(
    db_session: Any,
    config: RoundUpConfig,
    transaction: Transaction,
    round_up_amount: float
) -> Transaction:
    """Execute the round-up transfer"""
    # Create transfer transaction
    transfer = Transaction(
        account_id=config.source_account_id,
        amount=round_up_amount,
        transaction_type=TransactionType.TRANSFER,
        status=TransactionStatus.COMPLETED,
        description=f"Round-up from {transaction.description[:30]}",
        transaction_date=datetime.utcnow(),
        transfer_to_account_id=config.destination_account_id,
        category_id=16  # Assuming 16 is "Savings" category
    )

    # Update account balances
    source_account = db_session.query(Account).filter(Account.id == config.source_account_id).first()
    dest_account = db_session.query(Account).filter(Account.id == config.destination_account_id).first()

    source_account.balance -= round_up_amount
    dest_account.balance += round_up_amount

    db_session.add(transfer)
    return transfer

@router.post("/roundup", response_model=RoundUpConfigResponse, status_code=status.HTTP_201_CREATED)
async def configure_round_up(
    request: Request,
    config_data: RoundUpConfigRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Configure round-up savings"""

    # Verify account ownership
    source_account = db_session.query(Account).filter(
        Account.id == config_data.source_account_id,
        Account.user_id == current_user['user_id']
    ).first()

    dest_account = db_session.query(Account).filter(
        Account.id == config_data.destination_account_id,
        Account.user_id == current_user['user_id']
    ).first()

    if not source_account or not dest_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    if source_account.id == dest_account.id:
        raise ValidationError("Source and destination accounts must be different")

    # Check for existing active config
    existing = db_session.query(RoundUpConfig).filter(
        RoundUpConfig.user_id == current_user['user_id'],
        RoundUpConfig.source_account_id == config_data.source_account_id,
        RoundUpConfig.status == RoundUpStatus.ACTIVE
    ).first()

    if existing:
        raise ValidationError("Active round-up already exists for this account")

    # Create round-up config
    round_up_config = RoundUpConfig(
        user_id=current_user['user_id'],
        source_account_id=config_data.source_account_id,
        destination_account_id=config_data.destination_account_id,
        status=RoundUpStatus.ACTIVE,
        multiplier=config_data.multiplier,
        max_round_up_amount=config_data.max_round_up_amount,
        enabled_categories=config_data.enabled_categories
    )

    db_session.add(round_up_config)
    db_session.commit()
    db_session.refresh(round_up_config)

    return RoundUpConfigResponse.from_orm(round_up_config)

@router.get("/roundup/transactions", response_model=list[RoundUpTransactionResponse])
async def get_round_up_history(
    config_id: int | None = None,
    days: int = Query(30, ge=1, le=365),
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Get round-up transaction history"""
    since_date = datetime.utcnow() - timedelta(days=days)

    query = db_session.query(RoundUpTransaction).join(
        RoundUpConfig
    ).filter(
        RoundUpConfig.user_id == current_user['user_id'],
        RoundUpTransaction.created_at >= since_date
    )

    if config_id:
        query = query.filter(RoundUpTransaction.config_id == config_id)

    transactions = query.order_by(RoundUpTransaction.created_at.desc()).all()

    results = []
    for rt in transactions:
        # Get original transaction details
        original_tx = db_session.query(Transaction).filter(
            Transaction.id == rt.transaction_id
        ).first()

        if original_tx:
            response = RoundUpTransactionResponse(
                id=rt.id,
                transaction_id=rt.transaction_id,
                original_amount=rt.original_amount,
                round_up_amount=rt.round_up_amount,
                multiplied_amount=rt.multiplied_amount,
                transaction_date=rt.created_at,
                merchant_name=original_tx.description[:50],
                category_name=original_tx.category.name if original_tx.category else "Other"
            )
            results.append(response)

    return results

@router.post("/rules", response_model=SavingsRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_savings_rule(
    request: Request,
    rule_data: SavingsRuleRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Create an automated savings rule"""

    # Verify account ownership
    source_account = db_session.query(Account).filter(
        Account.id == rule_data.source_account_id,
        Account.user_id == current_user['user_id']
    ).first()

    dest_account = db_session.query(Account).filter(
        Account.id == rule_data.destination_account_id,
        Account.user_id == current_user['user_id']
    ).first()

    if not source_account or not dest_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Validate rule parameters
    if rule_data.rule_type == SavingsRuleType.PERCENTAGE and not rule_data.percentage:
        raise ValidationError("Percentage required for percentage-based rules")

    if rule_data.rule_type == SavingsRuleType.FIXED_AMOUNT and not rule_data.amount:
        raise ValidationError("Amount required for fixed amount rules")

    # Calculate next execution
    now = datetime.utcnow()
    if rule_data.frequency == SavingsRuleFrequency.DAILY:
        next_execution = now + timedelta(days=1)
    elif rule_data.frequency == SavingsRuleFrequency.WEEKLY:
        next_execution = now + timedelta(days=7)
    elif rule_data.frequency == SavingsRuleFrequency.BIWEEKLY:
        next_execution = now + timedelta(days=14)
    elif rule_data.frequency == SavingsRuleFrequency.MONTHLY:
        # Next month, same day
        if now.month == 12:
            next_execution = now.replace(year=now.year + 1, month=1)
        else:
            next_execution = now.replace(month=now.month + 1)
    else:  # PER_TRANSACTION
        next_execution = None

    # Create savings rule
    savings_rule = SavingsRule(
        user_id=current_user['user_id'],
        name=rule_data.name,
        rule_type=rule_data.rule_type,
        source_account_id=rule_data.source_account_id,
        destination_account_id=rule_data.destination_account_id,
        amount=rule_data.amount,
        percentage=rule_data.percentage,
        frequency=rule_data.frequency,
        trigger_conditions=rule_data.trigger_conditions,
        is_active=True,
        start_date=rule_data.start_date or now,
        end_date=rule_data.end_date,
        next_execution_at=next_execution
    )

    db_session.add(savings_rule)
    db_session.commit()
    db_session.refresh(savings_rule)

    return SavingsRuleResponse.from_orm(savings_rule)

@router.get("/rules", response_model=list[SavingsRuleResponse])
async def list_savings_rules(
    active_only: bool = True,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """List all savings rules"""
    query = db_session.query(SavingsRule).filter(
        SavingsRule.user_id == current_user['user_id']
    )

    if active_only:
        query = query.filter(SavingsRule.is_active == True)

    rules = query.order_by(SavingsRule.created_at.desc()).all()

    return [SavingsRuleResponse.from_orm(rule) for rule in rules]

@router.get("/challenges", response_model=list[SavingsChallengeResponse])
async def list_savings_challenges(
    status: ChallengeStatus | None = None,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """List available savings challenges"""
    query = db_session.query(SavingsChallenge)

    if status:
        query = query.filter(SavingsChallenge.status == status)
    else:
        # Show active and upcoming by default
        query = query.filter(
            SavingsChallenge.status.in_([ChallengeStatus.ACTIVE, ChallengeStatus.UPCOMING])
        )

    challenges = query.order_by(SavingsChallenge.start_date).all()

    results = []
    for challenge in challenges:
        # Get participant info
        participant = db_session.query(ChallengeParticipant).filter(
            ChallengeParticipant.challenge_id == challenge.id,
            ChallengeParticipant.user_id == current_user['user_id']
        ).first()

        # Count total participants
        participant_count = db_session.query(ChallengeParticipant).filter(
            ChallengeParticipant.challenge_id == challenge.id
        ).count()

        # Calculate current amount for all participants
        total_saved = db_session.query(
            db.func.sum(ChallengeParticipant.current_amount)
        ).filter(
            ChallengeParticipant.challenge_id == challenge.id
        ).scalar() or 0

        # Calculate user's position if participating
        leaderboard_position = None
        if participant:
            higher_savers = db_session.query(ChallengeParticipant).filter(
                ChallengeParticipant.challenge_id == challenge.id,
                ChallengeParticipant.current_amount > participant.current_amount
            ).count()
            leaderboard_position = higher_savers + 1

        response = SavingsChallengeResponse(
            id=challenge.id,
            name=challenge.name,
            description=challenge.description,
            challenge_type=challenge.challenge_type,
            status=challenge.status,
            target_amount=challenge.target_amount,
            current_amount=participant.current_amount if participant else 0,
            progress_percentage=(participant.current_amount / challenge.target_amount * 100) if participant else 0,
            participant_count=participant_count,
            start_date=challenge.start_date,
            end_date=challenge.end_date,
            reward_description=challenge.reward_description,
            rules=challenge.rules or [],
            leaderboard_position=leaderboard_position
        )
        results.append(response)

    return results

@router.post("/challenges/{challenge_id}/join", status_code=status.HTTP_201_CREATED)
async def join_savings_challenge(
    request: Request,
    challenge_id: int,
    join_data: ChallengeJoinRequest,
    current_user: dict = Depends(get_current_user),
    db_session: Any = Depends(db.get_db_dependency)
):
    """Join a savings challenge"""

    # Get challenge
    challenge = db_session.query(SavingsChallenge).filter(
        SavingsChallenge.id == challenge_id
    ).first()

    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found"
        )

    if challenge.status != ChallengeStatus.ACTIVE and challenge.status != ChallengeStatus.UPCOMING:
        raise ValidationError("Cannot join inactive challenge")

    # Check if already participating
    existing = db_session.query(ChallengeParticipant).filter(
        ChallengeParticipant.challenge_id == challenge_id,
        ChallengeParticipant.user_id == current_user['user_id']
    ).first()

    if existing:
        raise ValidationError("Already participating in this challenge")

    # Verify account ownership
    account = db_session.query(Account).filter(
        Account.id == join_data.account_id,
        Account.user_id == current_user['user_id']
    ).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    # Create participation
    participant = ChallengeParticipant(
        challenge_id=challenge_id,
        user_id=current_user['user_id'],
        commitment_amount=join_data.commitment_amount,
        account_id=join_data.account_id
    )

    db_session.add(participant)
    db_session.commit()

    return {"message": f"Successfully joined {challenge.name}"}

# Mock challenge creation for demo
def create_mock_challenges(db_session: Any):
    """Create some mock savings challenges"""
    challenges = [
        {
            "name": "52-Week Savings Challenge",
            "description": "Save increasing amounts each week for a year",
            "challenge_type": ChallengeType.WEEKLY_SAVINGS,
            "target_amount": 1378.00,  # Sum of 1+2+...+52
            "reward_description": "Complete to unlock premium savings features",
            "rules": [
                "Week 1: Save $1",
                "Week 2: Save $2",
                "Continue pattern for 52 weeks",
                "Total saved: $1,378"
            ]
        },
        {
            "name": "No-Spend November",
            "description": "Avoid non-essential spending for the month",
            "challenge_type": ChallengeType.NO_SPEND,
            "target_amount": 500.00,
            "reward_description": "Earn a 'Frugal Master' badge",
            "rules": [
                "No dining out",
                "No entertainment purchases",
                "No shopping except essentials",
                "Track all saved money"
            ]
        },
        {
            "name": "Round-Up Boost Week",
            "description": "Maximize your round-ups with 5x multiplier",
            "challenge_type": ChallengeType.ROUND_UP_BOOST,
            "target_amount": 50.00,
            "reward_description": "Keep 10% bonus on all round-ups",
            "rules": [
                "Enable 5x round-up multiplier",
                "Make at least 20 transactions",
                "Save minimum $50 via round-ups"
            ]
        }
    ]

    for idx, challenge_data in enumerate(challenges):
        # Check if already exists
        existing = db_session.query(SavingsChallenge).filter(
            SavingsChallenge.name == challenge_data["name"]
        ).first()

        if not existing:
            start_date = datetime.utcnow() + timedelta(days=idx * 7)

            if challenge_data["challenge_type"] == ChallengeType.WEEKLY_SAVINGS:
                end_date = start_date + timedelta(days=364)  # 52 weeks
            elif challenge_data["challenge_type"] == ChallengeType.NO_SPEND:
                end_date = start_date + timedelta(days=30)  # 1 month
            else:
                end_date = start_date + timedelta(days=7)  # 1 week

            challenge = SavingsChallenge(
                name=challenge_data["name"],
                description=challenge_data["description"],
                challenge_type=challenge_data["challenge_type"],
                status=ChallengeStatus.UPCOMING if idx > 0 else ChallengeStatus.ACTIVE,
                target_amount=challenge_data["target_amount"],
                reward_description=challenge_data["reward_description"],
                rules=challenge_data["rules"],
                start_date=start_date,
                end_date=end_date
            )

            db_session.add(challenge)

    db_session.commit()
