"""
Watchlist Service

Handles internal and external watchlist management and screening.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID, uuid4
import re

from ..models.watchlist_models import (
    WatchlistType, WatchlistCategory, EntityIdentifier, WatchlistEntry,
    Watchlist, WatchlistMatch, WatchlistScreeningRequest, WatchlistScreeningResult,
    WatchlistImport, WatchlistAuditLog, WatchlistStatistics
)


class WatchlistService:
    """Service for watchlist management and screening"""

    def __init__(self):
        self._watchlists: Dict[UUID, Watchlist] = {}
        self._entries: Dict[UUID, WatchlistEntry] = {}
        self._matches: Dict[UUID, WatchlistMatch] = {}
        self._audit_logs: List[WatchlistAuditLog] = []
        self._initialize_default_watchlists()

    def _initialize_default_watchlists(self):
        """Initialize default internal watchlists"""
        default_watchlists = [
            Watchlist(
                watchlist_name="High Risk Customers",
                watchlist_code="HIGH_RISK",
                watchlist_type=WatchlistType.INTERNAL,
                description="Customers identified as high risk requiring enhanced monitoring",
                default_category=WatchlistCategory.HIGH_RISK,
                owner_team="compliance",
                include_in_screening=True,
                created_by="system"
            ),
            Watchlist(
                watchlist_name="Exited Customers",
                watchlist_code="EXITED",
                watchlist_type=WatchlistType.INTERNAL,
                description="Customers who have been exited for compliance reasons",
                default_category=WatchlistCategory.EXITED,
                owner_team="compliance",
                include_in_screening=True,
                created_by="system"
            ),
            Watchlist(
                watchlist_name="Fraud Watch",
                watchlist_code="FRAUD_WATCH",
                watchlist_type=WatchlistType.INTERNAL,
                description="Entities with suspected or confirmed fraud involvement",
                default_category=WatchlistCategory.FRAUD,
                owner_team="fraud_team",
                include_in_screening=True,
                alert_severity="critical",
                created_by="system"
            ),
            Watchlist(
                watchlist_name="Do Not Onboard",
                watchlist_code="DNO",
                watchlist_type=WatchlistType.INTERNAL,
                description="Entities that should not be onboarded as customers",
                default_category=WatchlistCategory.DO_NOT_ONBOARD,
                owner_team="compliance",
                include_in_screening=True,
                alert_severity="critical",
                created_by="system"
            ),
        ]

        for watchlist in default_watchlists:
            self._watchlists[watchlist.watchlist_id] = watchlist

    async def create_watchlist(
        self, name: str, code: str, watchlist_type: WatchlistType, description: str,
        default_category: WatchlistCategory, owner_team: str, created_by: str, **kwargs
    ) -> Watchlist:
        """Create a new watchlist"""
        watchlist = Watchlist(
            watchlist_name=name,
            watchlist_code=code,
            watchlist_type=watchlist_type,
            description=description,
            default_category=default_category,
            owner_team=owner_team,
            created_by=created_by,
            **kwargs
        )

        self._watchlists[watchlist.watchlist_id] = watchlist

        # Audit log
        self._log_audit(
            watchlist.watchlist_id, None, "create",
            f"Watchlist '{name}' created", created_by
        )

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

    async def get_all_watchlists(self) -> List[Watchlist]:
        """Get all watchlists"""
        return list(self._watchlists.values())

    async def update_watchlist(
        self, watchlist_id: UUID, updates: Dict[str, Any], updated_by: str
    ) -> Optional[Watchlist]:
        """Update a watchlist"""
        watchlist = self._watchlists.get(watchlist_id)
        if not watchlist:
            return None

        old_values = {}
        for key, value in updates.items():
            if hasattr(watchlist, key):
                old_values[key] = getattr(watchlist, key)
                setattr(watchlist, key, value)

        watchlist.updated_at = datetime.utcnow()

        self._log_audit(
            watchlist_id, None, "update",
            f"Watchlist updated: {list(updates.keys())}",
            updated_by, old_values, updates
        )

        return watchlist

    async def add_entry(
        self, watchlist_id: UUID, entry_data: Dict[str, Any], created_by: str
    ) -> WatchlistEntry:
        """Add entry to a watchlist"""
        watchlist = self._watchlists.get(watchlist_id)
        if not watchlist:
            raise ValueError(f"Watchlist {watchlist_id} not found")

        entry = WatchlistEntry(
            watchlist_id=watchlist_id,
            entity_type=entry_data.get("entity_type", "individual"),
            primary_name=entry_data["primary_name"],
            aliases=entry_data.get("aliases", []),
            identifiers=[
                EntityIdentifier(**i) for i in entry_data.get("identifiers", [])
            ],
            date_of_birth=entry_data.get("date_of_birth"),
            nationalities=entry_data.get("nationalities", []),
            countries_of_residence=entry_data.get("countries_of_residence", []),
            category=entry_data.get("category", watchlist.default_category),
            risk_level=entry_data.get("risk_level", "high"),
            reason=entry_data["reason"],
            source=entry_data.get("source", "manual"),
            created_by=created_by
        )

        self._entries[entry.entry_id] = entry
        watchlist.entry_count += 1
        watchlist.active_entry_count += 1

        self._log_audit(
            watchlist_id, entry.entry_id, "create",
            f"Entry '{entry.primary_name}' added", created_by
        )

        return entry

    async def get_entry(self, entry_id: UUID) -> Optional[WatchlistEntry]:
        """Get watchlist entry by ID"""
        return self._entries.get(entry_id)

    async def update_entry(
        self, entry_id: UUID, updates: Dict[str, Any], updated_by: str
    ) -> Optional[WatchlistEntry]:
        """Update a watchlist entry"""
        entry = self._entries.get(entry_id)
        if not entry:
            return None

        old_values = {}
        for key, value in updates.items():
            if hasattr(entry, key):
                old_values[key] = getattr(entry, key)
                setattr(entry, key, value)

        entry.updated_by = updated_by
        entry.updated_at = datetime.utcnow()

        self._log_audit(
            entry.watchlist_id, entry_id, "update",
            f"Entry updated: {list(updates.keys())}",
            updated_by, old_values, updates
        )

        return entry

    async def deactivate_entry(
        self, entry_id: UUID, reason: str, deactivated_by: str
    ) -> Optional[WatchlistEntry]:
        """Deactivate a watchlist entry"""
        entry = self._entries.get(entry_id)
        if not entry:
            return None

        entry.is_active = False
        entry.status = "inactive"
        entry.updated_by = deactivated_by
        entry.updated_at = datetime.utcnow()
        entry.internal_notes = f"Deactivated: {reason}"

        watchlist = self._watchlists.get(entry.watchlist_id)
        if watchlist:
            watchlist.active_entry_count -= 1

        self._log_audit(
            entry.watchlist_id, entry_id, "deactivate",
            f"Entry deactivated: {reason}", deactivated_by
        )

        return entry

    async def search_entries(
        self, query: str, watchlist_ids: Optional[List[UUID]] = None,
        categories: Optional[List[WatchlistCategory]] = None,
        active_only: bool = True
    ) -> List[WatchlistEntry]:
        """Search watchlist entries"""
        results = []
        query_lower = query.lower()

        for entry in self._entries.values():
            if active_only and not entry.is_active:
                continue

            if watchlist_ids and entry.watchlist_id not in watchlist_ids:
                continue

            if categories and entry.category not in categories:
                continue

            # Search in name and aliases
            if query_lower in entry.primary_name.lower():
                results.append(entry)
                continue

            if any(query_lower in alias.lower() for alias in entry.aliases):
                results.append(entry)
                continue

            # Search in identifiers
            for identifier in entry.identifiers:
                if query_lower in identifier.identifier_value.lower():
                    results.append(entry)
                    break

        return results

    async def screen_entity(self, request: WatchlistScreeningRequest) -> WatchlistScreeningResult:
        """Screen an entity against watchlists"""
        result = WatchlistScreeningResult(
            request_id=request.request_id,
            entity_type=request.entity_type,
            entity_id=request.entity_id,
            entity_name=request.entity_name
        )

        watchlists_to_screen = request.watchlist_ids or list(self._watchlists.keys())
        entries_screened = 0
        matches = []

        for entry in self._entries.values():
            if entry.watchlist_id not in watchlists_to_screen:
                continue

            if not entry.is_active and not request.include_inactive:
                continue

            entries_screened += 1

            match = await self._check_match(request, entry)
            if match and match.match_score >= request.match_threshold:
                matches.append(match)
                self._matches[match.match_id] = match

        result.watchlists_screened = len(watchlists_to_screen)
        result.entries_screened = entries_screened
        result.matches = matches
        result.has_matches = len(matches) > 0
        result.match_count = len(matches)
        if matches:
            result.highest_match_score = max(m.match_score for m in matches)

        return result

    async def _check_match(
        self, request: WatchlistScreeningRequest, entry: WatchlistEntry
    ) -> Optional[WatchlistMatch]:
        """Check if request matches an entry"""
        # Name matching
        name_score = self._calculate_name_score(request.entity_name, entry.primary_name)

        # Check aliases
        for alias in request.aliases + entry.aliases:
            alias_score = self._calculate_name_score(request.entity_name, alias)
            name_score = max(name_score, alias_score)

        # Identifier matching
        identifier_score = 0.0
        matching_fields = ["name"]

        for req_id in request.identifiers:
            for entry_id in entry.identifiers:
                if (req_id.identifier_type == entry_id.identifier_type and
                    req_id.identifier_value.lower() == entry_id.identifier_value.lower()):
                    identifier_score = 1.0
                    matching_fields.append(f"identifier:{req_id.identifier_type}")
                    break

        # DOB matching
        dob_match = False
        if request.date_of_birth and entry.date_of_birth:
            dob_match = request.date_of_birth == entry.date_of_birth
            if dob_match:
                matching_fields.append("date_of_birth")

        # Nationality matching
        nationality_match = bool(
            set(request.nationalities) & set(entry.nationalities)
        ) if request.nationalities and entry.nationalities else False
        if nationality_match:
            matching_fields.append("nationality")

        # Calculate overall score
        overall_score = name_score * 0.6 + identifier_score * 0.3
        if dob_match:
            overall_score += 0.05
        if nationality_match:
            overall_score += 0.05

        if overall_score < 0.5:
            return None

        watchlist = self._watchlists.get(entry.watchlist_id)

        return WatchlistMatch(
            screened_entity_type=request.entity_type,
            screened_entity_id=request.entity_id or "",
            screened_entity_name=request.entity_name,
            screened_identifiers=request.identifiers,
            watchlist_id=entry.watchlist_id,
            watchlist_name=watchlist.watchlist_name if watchlist else "",
            entry_id=entry.entry_id,
            entry_name=entry.primary_name,
            entry_category=entry.category,
            match_score=overall_score,
            match_type="exact" if overall_score >= 0.95 else "fuzzy",
            matching_fields=matching_fields,
            name_score=name_score,
            identifier_score=identifier_score,
            dob_match=dob_match,
            nationality_match=nationality_match
        )

    def _calculate_name_score(self, name1: str, name2: str) -> float:
        """Calculate similarity score between two names"""
        name1_norm = re.sub(r'[^a-z\s]', '', name1.lower())
        name2_norm = re.sub(r'[^a-z\s]', '', name2.lower())

        if name1_norm == name2_norm:
            return 1.0

        tokens1 = set(name1_norm.split())
        tokens2 = set(name2_norm.split())

        if not tokens1 or not tokens2:
            return 0.0

        intersection = tokens1 & tokens2
        union = tokens1 | tokens2

        return len(intersection) / len(union)

    async def review_match(
        self, match_id: UUID, status: str, reviewed_by: str, notes: Optional[str] = None
    ) -> Optional[WatchlistMatch]:
        """Review a watchlist match"""
        match = self._matches.get(match_id)
        if not match:
            return None

        match.status = status
        match.reviewed_by = reviewed_by
        match.reviewed_at = datetime.utcnow()
        match.review_notes = notes

        return match

    async def import_entries(
        self, watchlist_id: UUID, entries_data: List[Dict[str, Any]], imported_by: str
    ) -> WatchlistImport:
        """Import multiple entries to a watchlist"""
        import_record = WatchlistImport(
            watchlist_id=watchlist_id,
            source_type="bulk_import",
            source_name="manual_import",
            total_records=len(entries_data),
            status="processing",
            created_by=imported_by
        )

        import_record.started_at = datetime.utcnow()

        for entry_data in entries_data:
            try:
                await self.add_entry(watchlist_id, entry_data, imported_by)
                import_record.imported_records += 1
            except Exception as e:
                import_record.failed_records += 1
                import_record.errors.append({
                    "entry": entry_data.get("primary_name", "Unknown"),
                    "error": str(e)
                })

        import_record.status = "completed"
        import_record.completed_at = datetime.utcnow()

        return import_record

    def _log_audit(
        self, watchlist_id: UUID, entry_id: Optional[UUID], action: str,
        details: str, performed_by: str,
        previous_values: Optional[Dict] = None, new_values: Optional[Dict] = None
    ):
        """Log audit entry"""
        audit = WatchlistAuditLog(
            watchlist_id=watchlist_id,
            entry_id=entry_id,
            action=action,
            action_details=details,
            previous_values=previous_values,
            new_values=new_values,
            performed_by=performed_by
        )
        self._audit_logs.append(audit)

    async def get_statistics(self) -> WatchlistStatistics:
        """Get watchlist statistics"""
        stats = WatchlistStatistics()
        stats.total_watchlists = len(self._watchlists)
        stats.total_entries = len(self._entries)
        stats.active_entries = len([e for e in self._entries.values() if e.is_active])

        for watchlist in self._watchlists.values():
            type_key = watchlist.watchlist_type.value
            stats.by_type[type_key] = stats.by_type.get(type_key, 0) + 1

        for entry in self._entries.values():
            category_key = entry.category.value
            stats.by_category[category_key] = stats.by_category.get(category_key, 0) + 1

        # Match statistics
        stats.pending_review = len([m for m in self._matches.values() if m.status == "pending"])

        return stats


# Global service instance
watchlist_service = WatchlistService()
