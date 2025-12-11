"""ML Model Repository - Data access layer for machine learning models"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from ..models.ml_models import (
    MLModel, ModelPrediction, ModelTrainingJob,
    ModelPerformanceMetrics, ModelType, ModelStatus
)


class MLModelRepository:
    def __init__(self):
        self._models: Dict[UUID, MLModel] = {}
        self._predictions: List[ModelPrediction] = []
        self._training_jobs: Dict[UUID, ModelTrainingJob] = {}
        self._metrics: Dict[UUID, List[ModelPerformanceMetrics]] = {}
        self._model_name_index: Dict[str, UUID] = {}

    async def save_model(self, model: MLModel) -> MLModel:
        self._models[model.model_id] = model
        model_key = f"{model.model_name}:{model.model_version}"
        self._model_name_index[model_key] = model.model_id
        return model

    async def find_model_by_id(self, model_id: UUID) -> Optional[MLModel]:
        return self._models.get(model_id)

    async def find_model_by_name_version(self, name: str, version: str) -> Optional[MLModel]:
        model_key = f"{name}:{version}"
        model_id = self._model_name_index.get(model_key)
        if model_id:
            return self._models.get(model_id)
        return None

    async def find_models_by_type(self, model_type: ModelType) -> List[MLModel]:
        return [m for m in self._models.values() if m.model_type == model_type]

    async def find_active_models(self) -> List[MLModel]:
        return [m for m in self._models.values() if m.status == ModelStatus.ACTIVE]

    async def find_models_by_status(self, status: ModelStatus) -> List[MLModel]:
        return [m for m in self._models.values() if m.status == status]

    async def update_model(self, model: MLModel) -> MLModel:
        model.updated_at = datetime.utcnow()
        self._models[model.model_id] = model
        return model

    async def delete_model(self, model_id: UUID) -> bool:
        if model_id in self._models:
            model = self._models[model_id]
            del self._models[model_id]
            model_key = f"{model.model_name}:{model.model_version}"
            if model_key in self._model_name_index:
                del self._model_name_index[model_key]
            return True
        return False

    async def save_prediction(self, prediction: ModelPrediction) -> ModelPrediction:
        self._predictions.append(prediction)
        return prediction

    async def find_predictions_by_model(self, model_id: UUID, limit: int = 100) -> List[ModelPrediction]:
        predictions = [p for p in self._predictions if p.model_id == model_id]
        return sorted(predictions, key=lambda x: x.predicted_at, reverse=True)[:limit]

    async def find_fraud_predictions(self, limit: int = 100) -> List[ModelPrediction]:
        predictions = [p for p in self._predictions if p.is_fraud]
        return sorted(predictions, key=lambda x: x.fraud_score, reverse=True)[:limit]

    async def find_recent_predictions(self, hours: int = 24, limit: int = 500) -> List[ModelPrediction]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        predictions = [p for p in self._predictions if p.predicted_at >= cutoff]
        return sorted(predictions, key=lambda x: x.predicted_at, reverse=True)[:limit]

    async def save_training_job(self, job: ModelTrainingJob) -> ModelTrainingJob:
        self._training_jobs[job.job_id] = job
        return job

    async def find_training_job_by_id(self, job_id: UUID) -> Optional[ModelTrainingJob]:
        return self._training_jobs.get(job_id)

    async def find_training_jobs_by_model(self, model_id: UUID) -> List[ModelTrainingJob]:
        jobs = [j for j in self._training_jobs.values() if j.model_id == model_id]
        return sorted(jobs, key=lambda x: x.started_at, reverse=True)

    async def find_running_jobs(self) -> List[ModelTrainingJob]:
        return [j for j in self._training_jobs.values() if j.status == "running"]

    async def update_training_job(self, job: ModelTrainingJob) -> ModelTrainingJob:
        self._training_jobs[job.job_id] = job
        return job

    async def save_metrics(self, model_id: UUID, metrics: ModelPerformanceMetrics) -> ModelPerformanceMetrics:
        if model_id not in self._metrics:
            self._metrics[model_id] = []
        self._metrics[model_id].append(metrics)
        return metrics

    async def find_metrics_by_model(self, model_id: UUID) -> List[ModelPerformanceMetrics]:
        return self._metrics.get(model_id, [])

    async def find_latest_metrics(self, model_id: UUID) -> Optional[ModelPerformanceMetrics]:
        metrics = self._metrics.get(model_id, [])
        if metrics:
            return sorted(metrics, key=lambda x: x.evaluated_at, reverse=True)[0]
        return None

    async def get_model_statistics(self) -> Dict[str, Any]:
        total_models = len(self._models)
        active_models = len([m for m in self._models.values() if m.status == ModelStatus.ACTIVE])
        by_type = {}
        for model in self._models.values():
            type_key = model.model_type.value
            by_type[type_key] = by_type.get(type_key, 0) + 1
        today = datetime.utcnow().date()
        predictions_today = len([p for p in self._predictions if p.predicted_at.date() == today])
        return {
            "total_models": total_models,
            "active_models": active_models,
            "by_type": by_type,
            "total_predictions": len(self._predictions),
            "predictions_today": predictions_today,
            "running_jobs": len([j for j in self._training_jobs.values() if j.status == "running"])
        }

    async def get_all_models(self, limit: int = 100, offset: int = 0) -> List[MLModel]:
        models = sorted(self._models.values(), key=lambda x: x.created_at, reverse=True)
        return models[offset:offset + limit]

    async def count_models(self) -> int:
        return len(self._models)


ml_model_repository = MLModelRepository()
