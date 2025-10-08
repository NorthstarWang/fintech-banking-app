"""
Base repository class providing common CRUD operations for in-memory data stores.
"""
import uuid
from abc import ABC
from datetime import datetime
from typing import Any, Generic, TypeVar

T = TypeVar('T', bound=dict[str, Any])

class BaseRepository(ABC, Generic[T]):
    """
    Abstract base class for repositories providing common CRUD operations.
    Works directly on in-memory Python lists.
    """

    def __init__(self, data_store: list[T]):
        """
        Initialize repository with a reference to the data store.
        
        Args:
            data_store: List that holds the entities
        """
        self.data_store = data_store

    def create(self, data: dict[str, Any]) -> T:
        """
        Create a new entity with auto-generated ID and timestamp.
        
        Args:
            data: Entity data without id and created_at
            
        Returns:
            Created entity with id and created_at
        """
        entity = data.copy()

        # Generate UUID if not provided
        if 'id' not in entity:
            entity['id'] = str(uuid.uuid4())

        # Add timestamp if not provided
        if 'created_at' not in entity:
            entity['created_at'] = datetime.utcnow().isoformat()

        # Add to data store
        self.data_store.append(entity)

        return entity

    def find_by_id(self, entity_id: str) -> T | None:
        """
        Find an entity by its ID.
        
        Args:
            entity_id: The ID to search for
            
        Returns:
            Entity if found, None otherwise
        """
        for entity in self.data_store:
            if entity.get('id') == entity_id:
                return entity.copy()
        return None

    def find_all(self) -> list[T]:
        """
        Get all entities.
        
        Returns:
            List of all entities (copies)
        """
        return [entity.copy() for entity in self.data_store]

    def find_by_field(self, field: str, value: Any) -> list[T]:
        """
        Find entities by a specific field value.
        
        Args:
            field: Field name to search by
            value: Value to match
            
        Returns:
            List of matching entities (copies)
        """
        return [
            entity.copy()
            for entity in self.data_store
            if entity.get(field) == value
        ]

    def find_one_by_field(self, field: str, value: Any) -> T | None:
        """
        Find first entity by a specific field value.
        
        Args:
            field: Field name to search by
            value: Value to match
            
        Returns:
            First matching entity or None
        """
        for entity in self.data_store:
            if entity.get(field) == value:
                return entity.copy()
        return None

    def update_by_id(self, entity_id: str, updates: dict[str, Any]) -> T | None:
        """
        Update an entity by ID.
        
        Args:
            entity_id: ID of entity to update
            updates: Fields to update
            
        Returns:
            Updated entity or None if not found
        """
        for i, entity in enumerate(self.data_store):
            if entity.get('id') == entity_id:
                # Update fields
                for key, value in updates.items():
                    entity[key] = value

                # Add updated_at timestamp
                if 'updated_at' not in updates:
                    entity['updated_at'] = datetime.utcnow().isoformat()

                return entity.copy()
        return None

    def delete_by_id(self, entity_id: str) -> bool:
        """
        Delete an entity by ID.
        
        Args:
            entity_id: ID of entity to delete
            
        Returns:
            True if deleted, False if not found
        """
        for i, entity in enumerate(self.data_store):
            if entity.get('id') == entity_id:
                self.data_store.pop(i)
                return True
        return False

    def delete_by_field(self, field: str, value: Any) -> int:
        """
        Delete all entities matching a field value.
        
        Args:
            field: Field name to match
            value: Value to match
            
        Returns:
            Number of entities deleted
        """
        initial_count = len(self.data_store)
        self.data_store[:] = [
            entity for entity in self.data_store
            if entity.get(field) != value
        ]
        return initial_count - len(self.data_store)

    def count(self) -> int:
        """
        Get total count of entities.
        
        Returns:
            Number of entities
        """
        return len(self.data_store)

    def count_by_field(self, field: str, value: Any) -> int:
        """
        Count entities by field value.
        
        Args:
            field: Field name to match
            value: Value to match
            
        Returns:
            Number of matching entities
        """
        return sum(1 for entity in self.data_store if entity.get(field) == value)

    def exists_by_field(self, field: str, value: Any) -> bool:
        """
        Check if any entity exists with field value.
        
        Args:
            field: Field name to check
            value: Value to match
            
        Returns:
            True if exists, False otherwise
        """
        return any(entity.get(field) == value for entity in self.data_store)

    def find_with_pagination(
        self,
        page: int = 1,
        page_size: int = 10,
        filters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Find entities with pagination support.
        
        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            filters: Optional field filters
            
        Returns:
            Dict with items, total, page, page_size
        """
        # Apply filters if provided
        filtered = self.data_store
        if filters:
            for field, value in filters.items():
                filtered = [e for e in filtered if e.get(field) == value]

        # Calculate pagination
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size

        return {
            'items': [e.copy() for e in filtered[start:end]],
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
