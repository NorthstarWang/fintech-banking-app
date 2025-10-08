"""
Service for automatic goal updates based on account transactions.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models import (
    Goal, GoalContribution, Transaction, Account,
    TransactionType, GoalStatus
)
from ..utils.money import format_money, safe_add_money
from ..storage.memory_adapter import db, desc


class GoalUpdateService:
    """Service to handle automatic goal contributions from transactions."""
    
    @staticmethod
    def process_transaction_for_goals(
        db_session: Any,
        transaction: Any,
        session_id: str = "system"
    ) -> List[Any]:
        """
        Process a transaction to check if it should trigger goal contributions.
        
        Args:
            db_session: Database session (memory adapter)
            transaction: The transaction to process
            session_id: Session ID for logging
            
        Returns:
            List of goal contributions created
        """
        contributions_created = []
        
        # Get transaction data
        trans_data = transaction._data if hasattr(transaction, '_data') else transaction
        
        # Only process credit transactions (deposits/income)
        if trans_data.get('transaction_type') != 'credit':
            return contributions_created
            
        # Skip transfers between user's own accounts to avoid double counting
        if trans_data.get('from_account_id') and trans_data.get('to_account_id'):
            return contributions_created
            
        # Get the account
        account = db_session.query(Account).filter(
            Account.id == trans_data.get('account_id')
        ).first()
        
        if not account:
            return contributions_created
            
        account_data = account._data if hasattr(account, '_data') else account
        
        # Find all active goals linked to this account
        linked_goals = db_session.query(Goal).filter(
            Goal.account_id == account_data.get('id'),
            Goal.status == 'active',
            Goal.user_id == account_data.get('user_id')
        ).order_by(desc(Goal.allocation_priority)).all()
        
        if not linked_goals:
            return contributions_created
            
        # Calculate total allocation
        remaining_amount = float(trans_data.get('amount', 0))
        
        for goal in linked_goals:
            if remaining_amount <= 0:
                break
                
            goal_data = goal._data if hasattr(goal, '_data') else goal
            
            # Skip if goal is already completed
            current = float(goal_data.get('current_amount', 0))
            target = float(goal_data.get('target_amount', 0))
            if current >= target:
                continue
                
            # Calculate contribution amount based on allocation type
            contribution_amount = 0.0
            auto_percent = float(goal_data.get('auto_allocate_percentage', 0))
            auto_fixed = float(goal_data.get('auto_allocate_fixed_amount', 0))
            
            if auto_percent > 0:
                # Percentage-based allocation
                contribution_amount = min(
                    remaining_amount * (auto_percent / 100),
                    remaining_amount,
                    target - current  # Don't over-contribute
                )
            elif auto_fixed > 0:
                # Fixed amount allocation
                contribution_amount = min(
                    auto_fixed,
                    remaining_amount,
                    target - current

            if contribution_amount > 0:
                # Create contribution
                contribution = GoalContribution(
                    goal_id=goal_data.get('id'),
                    amount=contribution_amount,
                    contribution_date=trans_data.get('transaction_date') or datetime.utcnow(),
                    notes=f"Automatic contribution from {trans_data.get('description') or 'deposit'}",
                    is_automatic=True,
                    source_transaction_id=trans_data.get('id')

                # Update goal amount
                goal_data['current_amount'] = safe_add_money(current, contribution_amount)
                
                # Check if goal is completed
                if goal_data['current_amount'] >= target:
                    goal_data['status'] = 'completed'
                    goal_data['completed_at'] = datetime.utcnow()
                    
                    # Log goal completion
                        session_id,
                        {
                            "text": f"Goal '{goal_data.get('name')}' completed automatically",
                            "custom_action": "goal_auto_completed",
                            "data": {
                                "goal_id": goal_data.get('id'),
                                "goal_name": goal_data.get('name'),
                                "target_amount": target,
                                "final_amount": goal_data['current_amount']
                            }

                goal_data['updated_at'] = datetime.utcnow()
                
                db_session.add(contribution)
                contributions_created.append(contribution)
                
                remaining_amount -= contribution_amount
                
                # Log automatic contribution
                    session_id,
                    {
                        "text": f"Automatic goal contribution created",
                        "custom_action": "goal_auto_contribution",
                        "data": {
                            "goal_id": goal_data.get('id'),
                            "goal_name": goal_data.get('name'),
                            "contribution_amount": contribution_amount,
                            "transaction_id": trans_data.get('id'),
                            "new_current_amount": goal_data['current_amount'],
                            "progress_percentage": (goal_data['current_amount'] / target) * 100 if target > 0 else 0
                        }

        # Commit all changes
        if contributions_created:
            db_session.commit()
            
        return contributions_created
    
    @staticmethod
    def get_allocation_summary(
        db_session: Any,
        account_id: int
    ) -> Dict[str, Any]:
        """
        Get a summary of automatic allocation rules for an account.
        
        Args:
            db_session: Database session
            account_id: Account ID to get summary for
            
        Returns:
            Dictionary with allocation summary
        """
        linked_goals = db_session.query(Goal).filter(
            Goal.account_id == account_id,
            Goal.status == 'active'
        ).order_by(desc(Goal.allocation_priority)).all()
        
        total_percentage = 0
        total_fixed = 0
        
        for goal in linked_goals:
            goal_data = goal._data if hasattr(goal, '_data') else goal
            total_percentage += float(goal_data.get('auto_allocate_percentage', 0))
            total_fixed += float(goal_data.get('auto_allocate_fixed_amount', 0))
        
        return {
            "account_id": account_id,
            "linked_goals_count": len(linked_goals),
            "total_percentage_allocation": total_percentage,
            "total_fixed_allocation": total_fixed,
            "goals": [
                {
                    "id": (goal._data if hasattr(goal, '_data') else goal).get('id'),
                    "name": (goal._data if hasattr(goal, '_data') else goal).get('name'),
                    "allocation_percentage": float((goal._data if hasattr(goal, '_data') else goal).get('auto_allocate_percentage', 0)),
                    "allocation_fixed_amount": float((goal._data if hasattr(goal, '_data') else goal).get('auto_allocate_fixed_amount', 0)),
                    "priority": (goal._data if hasattr(goal, '_data') else goal).get('allocation_priority', 1),
                    "current_amount": float((goal._data if hasattr(goal, '_data') else goal).get('current_amount', 0)),
                    "target_amount": float((goal._data if hasattr(goal, '_data') else goal).get('target_amount', 0)),
                    "progress_percentage": (
                        float((goal._data if hasattr(goal, '_data') else goal).get('current_amount', 0)) / 
                        float((goal._data if hasattr(goal, '_data') else goal).get('target_amount', 1)) * 100
                    ) if float((goal._data if hasattr(goal, '_data') else goal).get('target_amount', 0)) > 0 else 0
                }
                for goal in linked_goals
            ]

    @staticmethod
    def validate_allocation_rules(
        db_session: Any,
        account_id: int,
        goal_id: Optional[int] = None,
        new_percentage: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Validate that allocation rules don't exceed 100% for an account.
        
        Args:
            db_session: Database session
            account_id: Account ID to validate
            goal_id: Goal ID being updated (to exclude from calculation)
            new_percentage: New percentage to validate
            
        Returns:
            Dictionary with validation results
        """
        query = db_session.query(Goal).filter(
            Goal.account_id == account_id,
            Goal.status == 'active'

        if goal_id:
            query = query.filter(Goal.id != goal_id)
            
        linked_goals = query.all()
        
        current_total = 0
        for goal in linked_goals:
            goal_data = goal._data if hasattr(goal, '_data') else goal
            current_total += float(goal_data.get('auto_allocate_percentage', 0))
        
        total_with_new = current_total + (new_percentage or 0)
        
        return {
            "is_valid": total_with_new <= 100,
            "current_total_percentage": current_total,
            "new_total_percentage": total_with_new,
            "remaining_percentage": 100 - current_total,
            "message": (
                "Allocation rules are valid" if total_with_new <= 100
                else f"Total allocation would exceed 100% (current: {current_total}%, new total: {total_with_new}%)"
            )
        }