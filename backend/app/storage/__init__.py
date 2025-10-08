"""
Storage module that exports memory-based adapter for data persistence.
"""
from .memory_adapter import and_, db, desc, func, joinedload, or_

__all__ = ['and_', 'db', 'desc', 'func', 'joinedload', 'or_']
