"""Rating Service - Credit rating and grading"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from uuid import UUID
from ..models.rating_models import (
    CreditRating, RatingScale, RatingGrade, RatingModel,
    RatingMigration, RatingReview, RatingOverride, RatingStatistics,
    RatingType, RatingAgency, RatingOutlook
)


class RatingService:
    def __init__(self):
        self._ratings: Dict[UUID, CreditRating] = {}
        self._scales: Dict[UUID, RatingScale] = {}
        self._models: Dict[UUID, RatingModel] = {}
        self._migrations: List[RatingMigration] = []
        self._reviews: Dict[UUID, RatingReview] = {}
        self._overrides: Dict[UUID, RatingOverride] = {}
        self._entity_ratings: Dict[str, UUID] = {}
        self._initialize_scales()

    def _initialize_scales(self):
        internal_scale = RatingScale(
            scale_name="Internal Rating Scale",
            rating_agency=RatingAgency.INTERNAL,
            grades=[
                {"grade": "1", "description": "Exceptional", "pd_range": "0.00-0.03%"},
                {"grade": "2", "description": "Excellent", "pd_range": "0.03-0.10%"},
                {"grade": "3", "description": "Strong", "pd_range": "0.10-0.25%"},
                {"grade": "4", "description": "Good", "pd_range": "0.25-0.50%"},
                {"grade": "5", "description": "Adequate", "pd_range": "0.50-1.00%"},
                {"grade": "6", "description": "Acceptable", "pd_range": "1.00-2.00%"},
                {"grade": "7", "description": "Watch", "pd_range": "2.00-5.00%"},
                {"grade": "8", "description": "Substandard", "pd_range": "5.00-10.00%"},
                {"grade": "9", "description": "Doubtful", "pd_range": "10.00-20.00%"},
                {"grade": "10", "description": "Default", "pd_range": "100%"},
            ],
            default_grade="10",
            pd_mapping={
                "1": 0.0001, "2": 0.0005, "3": 0.0015, "4": 0.0035,
                "5": 0.0075, "6": 0.015, "7": 0.035, "8": 0.075,
                "9": 0.15, "10": 1.0
            },
            lgd_mapping={
                "1": 0.25, "2": 0.30, "3": 0.35, "4": 0.40,
                "5": 0.45, "6": 0.50, "7": 0.55, "8": 0.60,
                "9": 0.70, "10": 0.80
            },
            effective_date=date.today()
        )
        self._scales[internal_scale.scale_id] = internal_scale

    def _get_pd_for_grade(self, grade: str) -> float:
        for scale in self._scales.values():
            if grade in scale.pd_mapping:
                return scale.pd_mapping[grade]
        return 0.02

    def _get_lgd_for_grade(self, grade: str) -> float:
        for scale in self._scales.values():
            if grade in scale.lgd_mapping:
                return scale.lgd_mapping[grade]
        return 0.45

    def _determine_category(self, grade: str) -> str:
        try:
            grade_num = int(grade)
            if grade_num <= 4:
                return "investment_grade"
            elif grade_num <= 7:
                return "sub_investment_grade"
            else:
                return "default"
        except ValueError:
            return "sub_investment_grade"

    async def assign_rating(
        self, entity_id: str, entity_name: str, entity_type: str,
        rating_grade: str, rating_rationale: str, rated_by: str
    ) -> CreditRating:
        # Check for previous rating
        previous_rating = None
        previous_rating_id = self._entity_ratings.get(entity_id)
        if previous_rating_id:
            prev = self._ratings.get(previous_rating_id)
            if prev:
                previous_rating = prev.rating_grade

        pd = self._get_pd_for_grade(rating_grade)
        lgd = self._get_lgd_for_grade(rating_grade)

        rating = CreditRating(
            entity_id=entity_id,
            entity_name=entity_name,
            entity_type=entity_type,
            rating_type=RatingType.INTERNAL,
            rating_agency=RatingAgency.INTERNAL,
            rating_grade=rating_grade,
            rating_score=int(rating_grade) if rating_grade.isdigit() else 5,
            rating_category=self._determine_category(rating_grade),
            probability_of_default=pd,
            loss_given_default=lgd,
            rating_date=date.today(),
            effective_date=date.today(),
            review_date=date.today() + timedelta(days=365),
            previous_rating=previous_rating,
            rating_change="upgrade" if previous_rating and rating_grade < previous_rating else (
                "downgrade" if previous_rating and rating_grade > previous_rating else "new"
            ),
            rating_rationale=rating_rationale,
            rated_by=rated_by
        )

        self._ratings[rating.rating_id] = rating
        self._entity_ratings[entity_id] = rating.rating_id

        # Record migration if applicable
        if previous_rating and previous_rating != rating_grade:
            await self._record_migration(entity_id, entity_name, previous_rating, rating_grade)

        return rating

    async def _record_migration(
        self, entity_id: str, entity_name: str,
        from_rating: str, to_rating: str
    ) -> RatingMigration:
        migration_type = "upgrade" if to_rating < from_rating else "downgrade"
        try:
            steps = abs(int(to_rating) - int(from_rating))
        except ValueError:
            steps = 1

        migration = RatingMigration(
            entity_id=entity_id,
            entity_name=entity_name,
            from_rating=from_rating,
            to_rating=to_rating,
            migration_type=migration_type,
            migration_date=date.today(),
            migration_reason="Rating review",
            migration_steps=steps,
            previous_pd=self._get_pd_for_grade(from_rating),
            new_pd=self._get_pd_for_grade(to_rating)
        )
        self._migrations.append(migration)
        return migration

    async def get_rating(self, rating_id: UUID) -> Optional[CreditRating]:
        return self._ratings.get(rating_id)

    async def get_entity_rating(self, entity_id: str) -> Optional[CreditRating]:
        rating_id = self._entity_ratings.get(entity_id)
        if rating_id:
            return self._ratings.get(rating_id)
        return None

    async def update_outlook(
        self, rating_id: UUID, outlook: RatingOutlook
    ) -> Optional[CreditRating]:
        rating = self._ratings.get(rating_id)
        if rating:
            rating.outlook = outlook
            rating.updated_at = datetime.utcnow()
        return rating

    async def create_review(
        self, rating_id: UUID, review_type: str,
        proposed_rating: str, rating_action: str,
        recommendation: str, reviewed_by: str
    ) -> Optional[RatingReview]:
        rating = self._ratings.get(rating_id)
        if not rating:
            return None

        review = RatingReview(
            rating_id=rating_id,
            entity_id=rating.entity_id,
            review_type=review_type,
            review_date=date.today(),
            current_rating=rating.rating_grade,
            proposed_rating=proposed_rating,
            rating_action=rating_action,
            recommendation=recommendation,
            reviewed_by=reviewed_by,
            review_notes=""
        )
        self._reviews[review.review_id] = review
        return review

    async def apply_override(
        self, rating_id: UUID, override_rating: str,
        override_reason: str, override_type: str,
        approved_by: str
    ) -> Optional[RatingOverride]:
        rating = self._ratings.get(rating_id)
        if not rating:
            return None

        override = RatingOverride(
            rating_id=rating_id,
            entity_id=rating.entity_id,
            model_rating=rating.rating_grade,
            override_rating=override_rating,
            override_reason=override_reason,
            override_type=override_type,
            override_date=date.today(),
            expiry_date=date.today() + timedelta(days=365),
            approved_by=approved_by,
            approval_date=datetime.utcnow()
        )
        self._overrides[override.override_id] = override

        # Apply override to rating
        rating.rating_grade = override_rating
        rating.probability_of_default = self._get_pd_for_grade(override_rating)
        rating.updated_at = datetime.utcnow()

        return override

    async def get_ratings_by_grade(self, grade: str) -> List[CreditRating]:
        return [r for r in self._ratings.values() if r.rating_grade == grade]

    async def get_migrations(self, entity_id: str = None) -> List[RatingMigration]:
        if entity_id:
            return [m for m in self._migrations if m.entity_id == entity_id]
        return self._migrations

    async def get_statistics(self) -> RatingStatistics:
        stats = RatingStatistics(total_ratings=len(self._ratings))

        for rating in self._ratings.values():
            stats.by_grade[rating.rating_grade] = stats.by_grade.get(rating.rating_grade, 0) + 1
            stats.by_category[rating.rating_category] = stats.by_category.get(rating.rating_category, 0) + 1
            stats.by_outlook[rating.outlook.value] = stats.by_outlook.get(rating.outlook.value, 0) + 1

        # Count YTD migrations
        year_start = date(date.today().year, 1, 1)
        ytd_migrations = [m for m in self._migrations if m.migration_date >= year_start]
        stats.upgrades_ytd = len([m for m in ytd_migrations if m.migration_type == "upgrade"])
        stats.downgrades_ytd = len([m for m in ytd_migrations if m.migration_type == "downgrade"])
        stats.defaults_ytd = len([r for r in self._ratings.values() if r.rating_category == "default"])

        if self._ratings:
            stats.average_pd = sum(r.probability_of_default for r in self._ratings.values()) / len(self._ratings)

        return stats


rating_service = RatingService()
