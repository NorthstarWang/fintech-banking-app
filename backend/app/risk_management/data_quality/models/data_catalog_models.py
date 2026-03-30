"""Data Catalog Models"""

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class CatalogEntry(BaseModel):
    entry_id: UUID = Field(default_factory=uuid4)
    asset_name: str
    asset_type: str  # table, view, file, api, report, dashboard
    database: str = ""
    schema_name: str = ""
    description: str = ""
    business_description: str = ""
    technical_description: str = ""
    owner: str = ""
    steward: str = ""
    domain: str = ""
    classification: str = "internal"
    sensitivity_level: str = "low"
    tags: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    created_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = True


class SchemaDefinition(BaseModel):
    schema_id: UUID = Field(default_factory=uuid4)
    entry_id: UUID
    columns: list[dict[str, Any]] = Field(default_factory=list)
    primary_keys: list[str] = Field(default_factory=list)
    foreign_keys: list[dict[str, str]] = Field(default_factory=list)
    indexes: list[dict[str, Any]] = Field(default_factory=list)
    constraints: list[dict[str, Any]] = Field(default_factory=list)
    partitioning: dict[str, Any] | None = None
    schema_version: str = "1.0"
    last_modified: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DatasetUsage(BaseModel):
    usage_id: UUID = Field(default_factory=uuid4)
    entry_id: UUID
    user_id: str
    user_name: str
    department: str
    access_type: str  # query, export, api_call
    access_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    query_text: str = ""
    rows_accessed: int = 0
    duration_ms: int = 0


class DatasetRating(BaseModel):
    rating_id: UUID = Field(default_factory=uuid4)
    entry_id: UUID
    user_id: str
    rating: int  # 1-5
    review: str = ""
    rating_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    helpful_votes: int = 0


class DatasetComment(BaseModel):
    comment_id: UUID = Field(default_factory=uuid4)
    entry_id: UUID
    user_id: str
    user_name: str
    comment_text: str
    comment_type: str = "general"  # general, question, issue, suggestion
    parent_comment_id: UUID | None = None
    created_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_resolved: bool = False


class DatasetBookmark(BaseModel):
    bookmark_id: UUID = Field(default_factory=uuid4)
    entry_id: UUID
    user_id: str
    bookmark_name: str = ""
    notes: str = ""
    created_date: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SearchHistory(BaseModel):
    search_id: UUID = Field(default_factory=uuid4)
    user_id: str
    search_query: str
    filters_applied: dict[str, Any] = Field(default_factory=dict)
    results_count: int = 0
    search_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    clicked_results: list[UUID] = Field(default_factory=list)


class CatalogCollection(BaseModel):
    collection_id: UUID = Field(default_factory=uuid4)
    collection_name: str
    description: str
    owner: str
    visibility: str = "private"  # private, team, public
    entries: list[UUID] = Field(default_factory=list)
    collaborators: list[str] = Field(default_factory=list)
    created_date: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DataDictionary(BaseModel):
    dictionary_id: UUID = Field(default_factory=uuid4)
    entry_id: UUID
    column_name: str
    business_name: str
    description: str
    data_type: str
    format: str = ""
    allowed_values: list[str] = Field(default_factory=list)
    default_value: str = ""
    is_nullable: bool = True
    is_pii: bool = False
    is_sensitive: bool = False
    glossary_term_id: UUID | None = None
    owner: str = ""
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))
