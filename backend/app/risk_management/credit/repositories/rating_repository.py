"""Rating Repository - Data access layer for credit ratings"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from ..models.rating_models import (
    CreditRating, RatingScale, RatingGrade, RatingModel,
    RatingMigration, RatingReview, RatingOverride,
    RatingType, RatingAgency, RatingOutlook
)


class RatingRepository:
    def __init__(self):
        self._ratings: Dict[UUID, CreditRating] = {}
        self._scales: Dict[UUID, RatingScale] = {}
        self._models: Dict[UUID, RatingModel] = {}
        self._migrations: List[RatingMigration] = []
        self._reviews: Dict[UUID, RatingReview] = {}
        self._overrides: Dict[UUID, RatingOverride] = {}
        self._entity_index: Dict[str, UUID] = {}

    async def save(self, rating: CreditRating) -> CreditRating:
        self._ratings[rating.rating_id] = rating
        self._entity_index[rating.entity_id] = rating.rating_id
        return rating

    async def find_by_id(self, rating_id: UUID) -> Optional[CreditRating]:
        return self._ratings.get(rating_id)

    async def find_by_entity(self, entity_id: str) -> Optional[CreditRating]:
        rid = self._entity_index.get(entity_id)
        if rid:
            return self._ratings.get(rid)
        return None

    async def find_by_grade(self, grade: str) -> List[CreditRating]:
        return [r for r in self._ratings.values() if r.rating_grade == grade]

    async def find_by_category(self, category: str) -> List[CreditRating]:
        return [r for r in self._ratings.values() if r.rating_category == category]

    async def find_by_outlook(self, outlook: RatingOutlook) -> List[CreditRating]:
        return [r for r in self._ratings.values() if r.outlook == outlook]

    async def find_for_review(self) -> List[CreditRating]:
        today = date.today()
        return [r for r in self._ratings.values() if r.review_date <= today and r.status == "active"]

    async def find_expiring(self, days: int = 30) -> List[CreditRating]:
        from datetime import timedelta
        cutoff = date.today() + timedelta(days=days)
        return [r for r in self._ratings.values() if r.expiry_date and r.expiry_date <= cutoff]

    async def update(self, rating: CreditRating) -> CreditRating:
        rating.updated_at = datetime.utcnow()
        self._ratings[rating.rating_id] = rating
        return rating

    async def save_scale(self, scale: RatingScale) -> RatingScale:
        self._scales[scale.scale_id] = scale
        return scale

    async def find_scale_by_agency(self, agency: RatingAgency) -> Optional[RatingScale]:
        for scale in self._scales.values():
            if scale.rating_agency == agency:
                return scale
        return None

    async def save_model(self, model: RatingModel) -> RatingModel:
        self._models[model.model_id] = model
        return model

    async def find_model_by_id(self, model_id: UUID) -> Optional[RatingModel]:
        return self._models.get(model_id)

    async def find_active_models(self) -> List[RatingModel]:
        return [m for m in self._models.values() if m.status == "active"]

    async def save_migration(self, migration: RatingMigration) -> RatingMigration:
        self._migrations.append(migration)
        return migration

    async def find_migrations_by_entity(self, entity_id: str) -> List[RatingMigration]:
        return [m for m in self._migrations if m.entity_id == entity_id]

    async def find_recent_migrations(self, days: int = 90) -> List[RatingMigration]:
        from datetime import timedelta
        cutoff = date.today() - timedelta(days=days)
        return [m for m in self._migrations if m.migration_date >= cutoff]

    async def save_review(self, review: RatingReview) -> RatingReview:
        self._reviews[review.review_id] = review
        return review

    async def find_reviews_by_rating(self, rating_id: UUID) -> List[RatingReview]:
        return [r for r in self._reviews.values() if r.rating_id == rating_id]

    async def find_pending_reviews(self) -> List[RatingReview]:
        return [r for r in self._reviews.values() if r.status == "pending"]

    async def save_override(self, override: RatingOverride) -> RatingOverride:
        self._overrides[override.override_id] = override
        return override

    async def find_overrides_by_rating(self, rating_id: UUID) -> List[RatingOverride]:
        return [o for o in self._overrides.values() if o.rating_id == rating_id]

    async def find_active_overrides(self) -> List[RatingOverride]:
        today = date.today()
        return [o for o in self._overrides.values() if o.status == "active" and o.expiry_date >= today]

    async def get_statistics(self) -> Dict[str, Any]:
        by_grade = {}
        by_category = {}
        for rating in self._ratings.values():
            by_grade[rating.rating_grade] = by_grade.get(rating.rating_grade, 0) + 1
            by_category[rating.rating_category] = by_category.get(rating.rating_category, 0) + 1
        return {
            "total_ratings": len(self._ratings),
            "by_grade": by_grade,
            "by_category": by_category,
            "total_migrations": len(self._migrations)
        }

    async def count(self) -> int:
        return len(self._ratings)


rating_repository = RatingRepository()
