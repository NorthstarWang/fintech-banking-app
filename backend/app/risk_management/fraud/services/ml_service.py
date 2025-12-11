"""ML Service - Machine learning model management for fraud detection"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from ..models.ml_models import (
    MLModel, ModelPrediction, ModelTrainingJob,
    ModelPerformanceMetrics, ModelType, ModelStatus, MLModelStatistics
)


class MLService:
    def __init__(self):
        self._models: Dict[UUID, MLModel] = {}
        self._predictions: List[ModelPrediction] = []
        self._jobs: Dict[UUID, ModelTrainingJob] = {}

    async def register_model(self, name: str, model_type: ModelType, algorithm: str, created_by: str) -> MLModel:
        model = MLModel(
            model_name=name,
            model_type=model_type,
            model_version="1.0.0",
            description=f"{model_type.value} model using {algorithm}",
            algorithm=algorithm,
            framework="sklearn",
            created_by=created_by
        )
        self._models[model.model_id] = model
        return model

    async def get_model(self, model_id: UUID) -> Optional[MLModel]:
        return self._models.get(model_id)

    async def activate_model(self, model_id: UUID) -> Optional[MLModel]:
        model = self._models.get(model_id)
        if model:
            model.status = ModelStatus.ACTIVE
            model.activated_at = datetime.utcnow()
        return model

    async def deactivate_model(self, model_id: UUID) -> Optional[MLModel]:
        model = self._models.get(model_id)
        if model:
            model.status = ModelStatus.INACTIVE
        return model

    async def predict(self, model_id: UUID, input_data: Dict[str, Any]) -> Optional[ModelPrediction]:
        model = self._models.get(model_id)
        if not model or model.status != ModelStatus.ACTIVE:
            return None
        start_time = datetime.utcnow()
        # Simulate prediction
        fraud_probability = 0.3  # In production, would call actual model
        is_fraud = fraud_probability > model.threshold
        prediction = ModelPrediction(
            model_id=model_id,
            input_data=input_data,
            prediction=1 if is_fraud else 0,
            probability=fraud_probability,
            confidence=0.85,
            is_fraud=is_fraud,
            fraud_score=fraud_probability * 100,
            prediction_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
        )
        self._predictions.append(prediction)
        return prediction

    async def start_training_job(self, model_id: UUID, training_config: Dict[str, Any], created_by: str) -> ModelTrainingJob:
        job = ModelTrainingJob(
            model_id=model_id,
            training_config=training_config,
            status="running",
            started_at=datetime.utcnow(),
            total_epochs=training_config.get("epochs", 100),
            created_by=created_by
        )
        self._jobs[job.job_id] = job
        return job

    async def get_training_job(self, job_id: UUID) -> Optional[ModelTrainingJob]:
        return self._jobs.get(job_id)

    async def update_model_metrics(self, model_id: UUID, metrics: Dict[str, float]) -> Optional[MLModel]:
        model = self._models.get(model_id)
        if model:
            model.accuracy = metrics.get("accuracy", model.accuracy)
            model.precision = metrics.get("precision", model.precision)
            model.recall = metrics.get("recall", model.recall)
            model.f1_score = metrics.get("f1_score", model.f1_score)
            model.auc_roc = metrics.get("auc_roc", model.auc_roc)
        return model

    async def get_active_models(self) -> List[MLModel]:
        return [m for m in self._models.values() if m.status == ModelStatus.ACTIVE]

    async def get_statistics(self) -> MLModelStatistics:
        stats = MLModelStatistics(
            total_models=len(self._models),
            active_models=len([m for m in self._models.values() if m.status == ModelStatus.ACTIVE])
        )
        for model in self._models.values():
            stats.by_type[model.model_type.value] = stats.by_type.get(model.model_type.value, 0) + 1
        stats.total_predictions_today = len([p for p in self._predictions if p.predicted_at.date() == datetime.utcnow().date()])
        return stats


ml_service = MLService()
