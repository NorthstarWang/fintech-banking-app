"""Data Catalog Repository"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from ..models.data_catalog_models import (
    CatalogEntry, SchemaDefinition, DatasetUsage, DatasetRating,
    DatasetComment, DatasetBookmark, SearchHistory, CatalogCollection, DataDictionary
)


class DataCatalogRepository:
    def __init__(self):
        self._entries: Dict[UUID, CatalogEntry] = {}
        self._schemas: Dict[UUID, SchemaDefinition] = {}
        self._usages: Dict[UUID, DatasetUsage] = {}
        self._ratings: Dict[UUID, DatasetRating] = {}
        self._comments: Dict[UUID, DatasetComment] = {}
        self._bookmarks: Dict[UUID, DatasetBookmark] = {}
        self._searches: Dict[UUID, SearchHistory] = {}
        self._collections: Dict[UUID, CatalogCollection] = {}
        self._dictionaries: Dict[UUID, DataDictionary] = {}

    async def save_entry(self, entry: CatalogEntry) -> CatalogEntry:
        self._entries[entry.entry_id] = entry
        return entry

    async def find_entry_by_id(self, entry_id: UUID) -> Optional[CatalogEntry]:
        return self._entries.get(entry_id)

    async def find_all_entries(self) -> List[CatalogEntry]:
        return list(self._entries.values())

    async def find_entries_by_type(self, asset_type: str) -> List[CatalogEntry]:
        return [e for e in self._entries.values() if e.asset_type == asset_type]

    async def find_entries_by_domain(self, domain: str) -> List[CatalogEntry]:
        return [e for e in self._entries.values() if e.domain == domain]

    async def find_entries_by_classification(self, classification: str) -> List[CatalogEntry]:
        return [e for e in self._entries.values() if e.classification == classification]

    async def find_entries_by_tag(self, tag: str) -> List[CatalogEntry]:
        return [e for e in self._entries.values() if tag in e.tags]

    async def delete_entry(self, entry_id: UUID) -> bool:
        if entry_id in self._entries:
            del self._entries[entry_id]
            return True
        return False

    async def save_schema(self, schema: SchemaDefinition) -> SchemaDefinition:
        self._schemas[schema.schema_id] = schema
        return schema

    async def find_schema_by_id(self, schema_id: UUID) -> Optional[SchemaDefinition]:
        return self._schemas.get(schema_id)

    async def find_all_schemas(self) -> List[SchemaDefinition]:
        return list(self._schemas.values())

    async def find_schema_by_entry(self, entry_id: UUID) -> Optional[SchemaDefinition]:
        for schema in self._schemas.values():
            if schema.entry_id == entry_id:
                return schema
        return None

    async def save_usage(self, usage: DatasetUsage) -> DatasetUsage:
        self._usages[usage.usage_id] = usage
        return usage

    async def find_usage_by_id(self, usage_id: UUID) -> Optional[DatasetUsage]:
        return self._usages.get(usage_id)

    async def find_all_usages(self) -> List[DatasetUsage]:
        return list(self._usages.values())

    async def find_usages_by_entry(self, entry_id: UUID) -> List[DatasetUsage]:
        return [u for u in self._usages.values() if u.entry_id == entry_id]

    async def find_usages_by_user(self, user_id: str) -> List[DatasetUsage]:
        return [u for u in self._usages.values() if u.user_id == user_id]

    async def save_rating(self, rating: DatasetRating) -> DatasetRating:
        self._ratings[rating.rating_id] = rating
        return rating

    async def find_rating_by_id(self, rating_id: UUID) -> Optional[DatasetRating]:
        return self._ratings.get(rating_id)

    async def find_all_ratings(self) -> List[DatasetRating]:
        return list(self._ratings.values())

    async def find_ratings_by_entry(self, entry_id: UUID) -> List[DatasetRating]:
        return [r for r in self._ratings.values() if r.entry_id == entry_id]

    async def get_average_rating(self, entry_id: UUID) -> float:
        ratings = await self.find_ratings_by_entry(entry_id)
        if not ratings:
            return 0.0
        return sum(r.rating for r in ratings) / len(ratings)

    async def save_comment(self, comment: DatasetComment) -> DatasetComment:
        self._comments[comment.comment_id] = comment
        return comment

    async def find_comment_by_id(self, comment_id: UUID) -> Optional[DatasetComment]:
        return self._comments.get(comment_id)

    async def find_all_comments(self) -> List[DatasetComment]:
        return list(self._comments.values())

    async def find_comments_by_entry(self, entry_id: UUID) -> List[DatasetComment]:
        return [c for c in self._comments.values() if c.entry_id == entry_id]

    async def save_bookmark(self, bookmark: DatasetBookmark) -> DatasetBookmark:
        self._bookmarks[bookmark.bookmark_id] = bookmark
        return bookmark

    async def find_bookmark_by_id(self, bookmark_id: UUID) -> Optional[DatasetBookmark]:
        return self._bookmarks.get(bookmark_id)

    async def find_all_bookmarks(self) -> List[DatasetBookmark]:
        return list(self._bookmarks.values())

    async def find_bookmarks_by_user(self, user_id: str) -> List[DatasetBookmark]:
        return [b for b in self._bookmarks.values() if b.user_id == user_id]

    async def find_bookmark_by_user_and_entry(self, user_id: str, entry_id: UUID) -> Optional[DatasetBookmark]:
        for bookmark in self._bookmarks.values():
            if bookmark.user_id == user_id and bookmark.entry_id == entry_id:
                return bookmark
        return None

    async def delete_bookmark(self, bookmark_id: UUID) -> bool:
        if bookmark_id in self._bookmarks:
            del self._bookmarks[bookmark_id]
            return True
        return False

    async def save_search(self, search: SearchHistory) -> SearchHistory:
        self._searches[search.search_id] = search
        return search

    async def find_search_by_id(self, search_id: UUID) -> Optional[SearchHistory]:
        return self._searches.get(search_id)

    async def find_all_searches(self) -> List[SearchHistory]:
        return list(self._searches.values())

    async def find_searches_by_user(self, user_id: str) -> List[SearchHistory]:
        return [s for s in self._searches.values() if s.user_id == user_id]

    async def get_popular_searches(self, limit: int = 10) -> List[str]:
        query_counts: Dict[str, int] = {}
        for search in self._searches.values():
            query = search.search_query.lower()
            query_counts[query] = query_counts.get(query, 0) + 1
        sorted_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)
        return [q[0] for q in sorted_queries[:limit]]

    async def save_collection(self, collection: CatalogCollection) -> CatalogCollection:
        self._collections[collection.collection_id] = collection
        return collection

    async def find_collection_by_id(self, collection_id: UUID) -> Optional[CatalogCollection]:
        return self._collections.get(collection_id)

    async def find_all_collections(self) -> List[CatalogCollection]:
        return list(self._collections.values())

    async def find_collections_by_owner(self, owner: str) -> List[CatalogCollection]:
        return [c for c in self._collections.values() if c.owner == owner]

    async def find_public_collections(self) -> List[CatalogCollection]:
        return [c for c in self._collections.values() if c.visibility == "public"]

    async def delete_collection(self, collection_id: UUID) -> bool:
        if collection_id in self._collections:
            del self._collections[collection_id]
            return True
        return False

    async def save_dictionary_entry(self, dictionary: DataDictionary) -> DataDictionary:
        self._dictionaries[dictionary.dictionary_id] = dictionary
        return dictionary

    async def find_dictionary_entry_by_id(self, dictionary_id: UUID) -> Optional[DataDictionary]:
        return self._dictionaries.get(dictionary_id)

    async def find_all_dictionary_entries(self) -> List[DataDictionary]:
        return list(self._dictionaries.values())

    async def find_dictionary_entries_by_entry(self, entry_id: UUID) -> List[DataDictionary]:
        return [d for d in self._dictionaries.values() if d.entry_id == entry_id]

    async def find_pii_columns(self) -> List[DataDictionary]:
        return [d for d in self._dictionaries.values() if d.is_pii]

    async def find_sensitive_columns(self) -> List[DataDictionary]:
        return [d for d in self._dictionaries.values() if d.is_sensitive]

    async def get_statistics(self) -> Dict[str, Any]:
        return {
            "total_entries": len(self._entries),
            "total_schemas": len(self._schemas),
            "total_usages": len(self._usages),
            "total_ratings": len(self._ratings),
            "total_comments": len(self._comments),
            "total_bookmarks": len(self._bookmarks),
            "total_searches": len(self._searches),
            "total_collections": len(self._collections),
            "public_collections": len([c for c in self._collections.values() if c.visibility == "public"]),
            "total_dictionary_entries": len(self._dictionaries),
            "pii_columns": len([d for d in self._dictionaries.values() if d.is_pii]),
        }


data_catalog_repository = DataCatalogRepository()
