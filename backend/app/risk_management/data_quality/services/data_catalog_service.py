"""Data Catalog Service"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from ..models.data_catalog_models import (
    CatalogEntry, SchemaDefinition, DatasetUsage, DatasetRating,
    DatasetComment, DatasetBookmark, SearchHistory, CatalogCollection, DataDictionary
)
from ..repositories.data_catalog_repository import data_catalog_repository


class DataCatalogService:
    def __init__(self):
        self.repository = data_catalog_repository

    async def create_catalog_entry(
        self, asset_name: str, asset_type: str, database: str = "",
        schema_name: str = "", description: str = "", business_description: str = "",
        owner: str = "", steward: str = "", domain: str = "",
        classification: str = "internal", tags: List[str] = None
    ) -> CatalogEntry:
        entry = CatalogEntry(
            asset_name=asset_name, asset_type=asset_type, database=database,
            schema_name=schema_name, description=description,
            business_description=business_description, owner=owner, steward=steward,
            domain=domain, classification=classification, tags=tags or []
        )
        await self.repository.save_entry(entry)
        return entry

    async def define_schema(
        self, entry_id: UUID, columns: List[Dict[str, Any]],
        primary_keys: List[str], foreign_keys: List[Dict[str, str]] = None
    ) -> SchemaDefinition:
        schema = SchemaDefinition(
            entry_id=entry_id, columns=columns, primary_keys=primary_keys,
            foreign_keys=foreign_keys or []
        )
        await self.repository.save_schema(schema)
        return schema

    async def record_usage(
        self, entry_id: UUID, user_id: str, user_name: str, department: str,
        access_type: str, query_text: str = "", rows_accessed: int = 0
    ) -> DatasetUsage:
        usage = DatasetUsage(
            entry_id=entry_id, user_id=user_id, user_name=user_name,
            department=department, access_type=access_type,
            query_text=query_text, rows_accessed=rows_accessed
        )
        await self.repository.save_usage(usage)
        return usage

    async def add_rating(
        self, entry_id: UUID, user_id: str, rating: int, review: str = ""
    ) -> DatasetRating:
        rating_obj = DatasetRating(
            entry_id=entry_id, user_id=user_id, rating=rating, review=review
        )
        await self.repository.save_rating(rating_obj)
        return rating_obj

    async def add_comment(
        self, entry_id: UUID, user_id: str, user_name: str,
        comment_text: str, comment_type: str = "general"
    ) -> DatasetComment:
        comment = DatasetComment(
            entry_id=entry_id, user_id=user_id, user_name=user_name,
            comment_text=comment_text, comment_type=comment_type
        )
        await self.repository.save_comment(comment)
        return comment

    async def bookmark_dataset(
        self, entry_id: UUID, user_id: str, bookmark_name: str = "", notes: str = ""
    ) -> DatasetBookmark:
        bookmark = DatasetBookmark(
            entry_id=entry_id, user_id=user_id, bookmark_name=bookmark_name, notes=notes
        )
        await self.repository.save_bookmark(bookmark)
        return bookmark

    async def record_search(
        self, user_id: str, search_query: str, filters_applied: Dict[str, Any],
        results_count: int, clicked_results: List[UUID] = None
    ) -> SearchHistory:
        search = SearchHistory(
            user_id=user_id, search_query=search_query, filters_applied=filters_applied,
            results_count=results_count, clicked_results=clicked_results or []
        )
        await self.repository.save_search(search)
        return search

    async def create_collection(
        self, collection_name: str, description: str, owner: str,
        visibility: str = "private", entries: List[UUID] = None
    ) -> CatalogCollection:
        collection = CatalogCollection(
            collection_name=collection_name, description=description, owner=owner,
            visibility=visibility, entries=entries or []
        )
        await self.repository.save_collection(collection)
        return collection

    async def add_to_collection(
        self, collection_id: UUID, entry_id: UUID
    ) -> Optional[CatalogCollection]:
        collection = await self.repository.find_collection_by_id(collection_id)
        if collection and entry_id not in collection.entries:
            collection.entries.append(entry_id)
            collection.last_updated = datetime.utcnow()
        return collection

    async def add_data_dictionary_entry(
        self, entry_id: UUID, column_name: str, business_name: str,
        description: str, data_type: str, is_pii: bool = False,
        is_sensitive: bool = False, owner: str = ""
    ) -> DataDictionary:
        dictionary = DataDictionary(
            entry_id=entry_id, column_name=column_name, business_name=business_name,
            description=description, data_type=data_type, is_pii=is_pii,
            is_sensitive=is_sensitive, owner=owner
        )
        await self.repository.save_dictionary_entry(dictionary)
        return dictionary

    async def search_catalog(self, query: str, filters: Dict[str, Any] = None) -> List[CatalogEntry]:
        entries = await self.repository.find_all_entries()
        query_lower = query.lower()
        results = [
            e for e in entries
            if query_lower in e.asset_name.lower()
            or query_lower in e.description.lower()
            or any(query_lower in tag.lower() for tag in e.tags)
        ]
        return results

    async def get_statistics(self) -> Dict[str, Any]:
        return await self.repository.get_statistics()


data_catalog_service = DataCatalogService()
