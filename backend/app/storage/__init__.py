"""
Storage module that exports memory-based adapter for data persistence.
"""
from .memory_adapter import db, or_, and_, desc, joinedload, func

__all__ = ['db', 'or_', 'and_', 'desc', 'joinedload', 'func']
