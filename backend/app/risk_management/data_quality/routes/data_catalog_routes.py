"""Data Catalog Routes"""

from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..services.data_catalog_service import data_catalog_service

router = APIRouter(prefix="/data-catalog", tags=["Data Catalog"])


class CreateEntryRequest(BaseModel):
    asset_name: str
    asset_type: str
    database: str = ""
    schema_name: str = ""
    description: str = ""
    business_description: str = ""
    owner: str = ""
    steward: str = ""
    domain: str = ""
    classification: str = "internal"
    tags: List[str] = []


class DefineSchemaRequest(BaseModel):
    entry_id: UUID
    columns: List[Dict[str, Any]]
    primary_keys: List[str]
    foreign_keys: List[Dict[str, str]] = []


class RecordUsageRequest(BaseModel):
    entry_id: UUID
    user_id: str
    user_name: str
    department: str
    access_type: str
    query_text: str = ""
    rows_accessed: int = 0


class AddRatingRequest(BaseModel):
    entry_id: UUID
    user_id: str
    rating: int
    review: str = ""


class AddCommentRequest(BaseModel):
    entry_id: UUID
    user_id: str
    user_name: str
    comment_text: str
    comment_type: str = "general"


class BookmarkDatasetRequest(BaseModel):
    entry_id: UUID
    user_id: str
    bookmark_name: str = ""
    notes: str = ""


class RecordSearchRequest(BaseModel):
    user_id: str
    search_query: str
    filters_applied: Dict[str, Any]
    results_count: int
    clicked_results: List[UUID] = []


class CreateCollectionRequest(BaseModel):
    collection_name: str
    description: str
    owner: str
    visibility: str = "private"
    entries: List[UUID] = []


class AddDictionaryEntryRequest(BaseModel):
    entry_id: UUID
    column_name: str
    business_name: str
    description: str
    data_type: str
    is_pii: bool = False
    is_sensitive: bool = False
    owner: str = ""


@router.post("/entries")
async def create_entry(request: CreateEntryRequest):
    entry = await data_catalog_service.create_catalog_entry(
        asset_name=request.asset_name,
        asset_type=request.asset_type,
        database=request.database,
        schema_name=request.schema_name,
        description=request.description,
        business_description=request.business_description,
        owner=request.owner,
        steward=request.steward,
        domain=request.domain,
        classification=request.classification,
        tags=request.tags,
    )
    return {"status": "created", "entry_id": str(entry.entry_id)}


@router.get("/entries")
async def get_all_entries():
    entries = await data_catalog_service.repository.find_all_entries()
    return {"entries": [{"entry_id": str(e.entry_id), "name": e.asset_name, "type": e.asset_type} for e in entries]}


@router.get("/entries/{entry_id}")
async def get_entry(entry_id: UUID):
    entry = await data_catalog_service.repository.find_entry_by_id(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.get("/entries/search")
async def search_entries(query: str):
    entries = await data_catalog_service.search_catalog(query)
    return {"entries": [{"entry_id": str(e.entry_id), "name": e.asset_name, "type": e.asset_type} for e in entries]}


@router.get("/entries/domain/{domain}")
async def get_entries_by_domain(domain: str):
    entries = await data_catalog_service.repository.find_entries_by_domain(domain)
    return {"entries": [{"entry_id": str(e.entry_id), "name": e.asset_name} for e in entries]}


@router.get("/entries/tag/{tag}")
async def get_entries_by_tag(tag: str):
    entries = await data_catalog_service.repository.find_entries_by_tag(tag)
    return {"entries": [{"entry_id": str(e.entry_id), "name": e.asset_name} for e in entries]}


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: UUID):
    deleted = await data_catalog_service.repository.delete_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"status": "deleted"}


@router.post("/schemas")
async def define_schema(request: DefineSchemaRequest):
    schema = await data_catalog_service.define_schema(
        entry_id=request.entry_id,
        columns=request.columns,
        primary_keys=request.primary_keys,
        foreign_keys=request.foreign_keys,
    )
    return {"status": "defined", "schema_id": str(schema.schema_id)}


@router.get("/schemas")
async def get_all_schemas():
    schemas = await data_catalog_service.repository.find_all_schemas()
    return {"schemas": [{"schema_id": str(s.schema_id), "entry_id": str(s.entry_id)} for s in schemas]}


@router.get("/schemas/entry/{entry_id}")
async def get_schema_by_entry(entry_id: UUID):
    schema = await data_catalog_service.repository.find_schema_by_entry(entry_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    return schema


@router.post("/usage")
async def record_usage(request: RecordUsageRequest):
    usage = await data_catalog_service.record_usage(
        entry_id=request.entry_id,
        user_id=request.user_id,
        user_name=request.user_name,
        department=request.department,
        access_type=request.access_type,
        query_text=request.query_text,
        rows_accessed=request.rows_accessed,
    )
    return {"status": "recorded", "usage_id": str(usage.usage_id)}


@router.get("/usage")
async def get_all_usage():
    usages = await data_catalog_service.repository.find_all_usages()
    return {"usages": [{"usage_id": str(u.usage_id), "entry_id": str(u.entry_id), "user": u.user_name} for u in usages]}


@router.get("/usage/entry/{entry_id}")
async def get_usage_by_entry(entry_id: UUID):
    usages = await data_catalog_service.repository.find_usages_by_entry(entry_id)
    return {"usages": [{"usage_id": str(u.usage_id), "user": u.user_name, "access_type": u.access_type} for u in usages]}


@router.post("/ratings")
async def add_rating(request: AddRatingRequest):
    rating = await data_catalog_service.add_rating(
        entry_id=request.entry_id,
        user_id=request.user_id,
        rating=request.rating,
        review=request.review,
    )
    return {"status": "added", "rating_id": str(rating.rating_id)}


@router.get("/ratings/entry/{entry_id}")
async def get_ratings_by_entry(entry_id: UUID):
    ratings = await data_catalog_service.repository.find_ratings_by_entry(entry_id)
    avg = await data_catalog_service.repository.get_average_rating(entry_id)
    return {"ratings": [{"rating_id": str(r.rating_id), "rating": r.rating} for r in ratings], "average": avg}


@router.post("/comments")
async def add_comment(request: AddCommentRequest):
    comment = await data_catalog_service.add_comment(
        entry_id=request.entry_id,
        user_id=request.user_id,
        user_name=request.user_name,
        comment_text=request.comment_text,
        comment_type=request.comment_type,
    )
    return {"status": "added", "comment_id": str(comment.comment_id)}


@router.get("/comments/entry/{entry_id}")
async def get_comments_by_entry(entry_id: UUID):
    comments = await data_catalog_service.repository.find_comments_by_entry(entry_id)
    return {"comments": [{"comment_id": str(c.comment_id), "user": c.user_name, "text": c.comment_text} for c in comments]}


@router.post("/bookmarks")
async def bookmark_dataset(request: BookmarkDatasetRequest):
    bookmark = await data_catalog_service.bookmark_dataset(
        entry_id=request.entry_id,
        user_id=request.user_id,
        bookmark_name=request.bookmark_name,
        notes=request.notes,
    )
    return {"status": "bookmarked", "bookmark_id": str(bookmark.bookmark_id)}


@router.get("/bookmarks/user/{user_id}")
async def get_user_bookmarks(user_id: str):
    bookmarks = await data_catalog_service.repository.find_bookmarks_by_user(user_id)
    return {"bookmarks": [{"bookmark_id": str(b.bookmark_id), "entry_id": str(b.entry_id), "name": b.bookmark_name} for b in bookmarks]}


@router.delete("/bookmarks/{bookmark_id}")
async def delete_bookmark(bookmark_id: UUID):
    deleted = await data_catalog_service.repository.delete_bookmark(bookmark_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    return {"status": "deleted"}


@router.post("/searches")
async def record_search(request: RecordSearchRequest):
    search = await data_catalog_service.record_search(
        user_id=request.user_id,
        search_query=request.search_query,
        filters_applied=request.filters_applied,
        results_count=request.results_count,
        clicked_results=request.clicked_results,
    )
    return {"status": "recorded", "search_id": str(search.search_id)}


@router.get("/searches/popular")
async def get_popular_searches(limit: int = 10):
    searches = await data_catalog_service.repository.get_popular_searches(limit)
    return {"popular_searches": searches}


@router.post("/collections")
async def create_collection(request: CreateCollectionRequest):
    collection = await data_catalog_service.create_collection(
        collection_name=request.collection_name,
        description=request.description,
        owner=request.owner,
        visibility=request.visibility,
        entries=request.entries,
    )
    return {"status": "created", "collection_id": str(collection.collection_id)}


@router.post("/collections/{collection_id}/add/{entry_id}")
async def add_to_collection(collection_id: UUID, entry_id: UUID):
    collection = await data_catalog_service.add_to_collection(
        collection_id=collection_id,
        entry_id=entry_id,
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")
    return {"status": "added", "collection_id": str(collection.collection_id)}


@router.get("/collections")
async def get_all_collections():
    collections = await data_catalog_service.repository.find_all_collections()
    return {"collections": [{"id": str(c.collection_id), "name": c.collection_name, "visibility": c.visibility} for c in collections]}


@router.get("/collections/public")
async def get_public_collections():
    collections = await data_catalog_service.repository.find_public_collections()
    return {"collections": [{"id": str(c.collection_id), "name": c.collection_name} for c in collections]}


@router.delete("/collections/{collection_id}")
async def delete_collection(collection_id: UUID):
    deleted = await data_catalog_service.repository.delete_collection(collection_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Collection not found")
    return {"status": "deleted"}


@router.post("/dictionary")
async def add_dictionary_entry(request: AddDictionaryEntryRequest):
    dictionary = await data_catalog_service.add_data_dictionary_entry(
        entry_id=request.entry_id,
        column_name=request.column_name,
        business_name=request.business_name,
        description=request.description,
        data_type=request.data_type,
        is_pii=request.is_pii,
        is_sensitive=request.is_sensitive,
        owner=request.owner,
    )
    return {"status": "added", "dictionary_id": str(dictionary.dictionary_id)}


@router.get("/dictionary/entry/{entry_id}")
async def get_dictionary_by_entry(entry_id: UUID):
    entries = await data_catalog_service.repository.find_dictionary_entries_by_entry(entry_id)
    return {"dictionary": [{"id": str(d.dictionary_id), "column": d.column_name, "business_name": d.business_name} for d in entries]}


@router.get("/dictionary/pii")
async def get_pii_columns():
    columns = await data_catalog_service.repository.find_pii_columns()
    return {"pii_columns": [{"id": str(c.dictionary_id), "column": c.column_name, "entry_id": str(c.entry_id)} for c in columns]}


@router.get("/dictionary/sensitive")
async def get_sensitive_columns():
    columns = await data_catalog_service.repository.find_sensitive_columns()
    return {"sensitive_columns": [{"id": str(c.dictionary_id), "column": c.column_name} for c in columns]}


@router.get("/statistics")
async def get_statistics():
    return await data_catalog_service.get_statistics()
