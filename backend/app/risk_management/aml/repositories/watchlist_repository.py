"""
Watchlist Repository

Data access layer for watchlist management.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from ..models.watchlist_models import (
    Watchlist, WatchlistEntry, WatchlistType, WatchlistCategory,
    WatchlistMatch, WatchlistAuditLog
)


class WatchlistRepository:
    """Repository for watchlist data access"""

    def __init__(self):
        self._watchlists: Dict[UUID, Watchlist] = {}
        self._entries: Dict[UUID, WatchlistEntry] = {}
        self._matches: Dict[UUID, WatchlistMatch] = {}
        self._audit_logs: List[WatchlistAuditLog] = []

    async def create_watchlist(self, watchlist: Watchlist) -> Watchlist:
        """Create a new watchlist"""
        self._watchlists[watchlist.watchlist_id] = watchlist
        return watchlist

    async def get_watchlist(self, watchlist_id: UUID) -> Optional[Watchlist]:
        """Get watchlist by ID"""
        return self._watchlists.get(watchlist_id)

    async def get_watchlist_by_code(self, code: str) -> Optional[Watchlist]:
        """Get watchlist by code"""
        for watchlist in self._watchlists.values():
            if watchlist.watchlist_code == code:
                return watchlist
        return None

    async def update_watchlist(self, watchlist: Watchlist) -> Watchlist:
        """Update a watchlist"""
        self._watchlists[watchlist.watchlist_id] = watchlist
        return watchlist

    async def delete_watchlist(self, watchlist_id: UUID) -> bool:
        """Delete a watchlist"""
        if watchlist_id in self._watchlists:
            del self._watchlists[watchlist_id]
            return True
        return False

    async def get_all_watchlists(self) -> List[Watchlist]:
        """Get all watchlists"""
        return list(self._watchlists.values())

    async def find_active_watchlists(self) -> List[Watchlist]:
        """Find active watchlists"""
        return [w for w in self._watchlists.values() if w.is_active]

    async def create_entry(self, entry: WatchlistEntry) -> WatchlistEntry:
        """Create a watchlist entry"""
        self._entries[entry.entry_id] = entry
        return entry

    async def get_entry(self, entry_id: UUID) -> Optional[WatchlistEntry]:
        """Get entry by ID"""
        return self._entries.get(entry_id)

    async def update_entry(self, entry: WatchlistEntry) -> WatchlistEntry:
        """Update an entry"""
        self._entries[entry.entry_id] = entry
        return entry

    async def delete_entry(self, entry_id: UUID) -> bool:
        """Delete an entry"""
        if entry_id in self._entries:
            del self._entries[entry_id]
            return True
        return False

    async def find_entries_by_watchlist(self, watchlist_id: UUID) -> List[WatchlistEntry]:
        """Find entries by watchlist"""
        return [e for e in self._entries.values() if e.watchlist_id == watchlist_id]

    async def find_active_entries(self) -> List[WatchlistEntry]:
        """Find active entries"""
        return [e for e in self._entries.values() if e.is_active]

    async def find_entries_by_category(self, category: WatchlistCategory) -> List[WatchlistEntry]:
        """Find entries by category"""
        return [e for e in self._entries.values() if e.category == category]

    async def search_entries(self, query: str) -> List[WatchlistEntry]:
        """Search entries by name"""
        query_lower = query.lower()
        results = []
        for entry in self._entries.values():
            if query_lower in entry.primary_name.lower():
                results.append(entry)
                continue
            if any(query_lower in alias.lower() for alias in entry.aliases):
                results.append(entry)
        return results

    async def save_match(self, match: WatchlistMatch) -> WatchlistMatch:
        """Save a match result"""
        self._matches[match.match_id] = match
        return match

    async def get_match(self, match_id: UUID) -> Optional[WatchlistMatch]:
        """Get match by ID"""
        return self._matches.get(match_id)

    async def find_pending_matches(self) -> List[WatchlistMatch]:
        """Find pending review matches"""
        return [m for m in self._matches.values() if m.status == "pending"]

    async def find_matches_by_entity(self, entity_id: str) -> List[WatchlistMatch]:
        """Find matches by entity"""
        return [m for m in self._matches.values() if m.screened_entity_id == entity_id]

    async def add_audit_log(self, log: WatchlistAuditLog) -> WatchlistAuditLog:
        """Add audit log entry"""
        self._audit_logs.append(log)
        return log

    async def get_audit_logs(
        self, watchlist_id: Optional[UUID] = None, limit: int = 100
    ) -> List[WatchlistAuditLog]:
        """Get audit logs"""
        logs = self._audit_logs
        if watchlist_id:
            logs = [l for l in logs if l.watchlist_id == watchlist_id]
        return logs[-limit:]

    async def count_entries(self) -> int:
        """Count total entries"""
        return len(self._entries)


# Global repository instance
watchlist_repository = WatchlistRepository()
