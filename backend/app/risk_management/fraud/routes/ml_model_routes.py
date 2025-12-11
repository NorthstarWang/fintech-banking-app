"""ML Model Routes - API endpoints for machine learning model management"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ..models.ml_models import (
    MLModel, ModelPrediction, ModelTrainingJob,
    ModelType, ModelStatus
)
from ..services.ml_service import ml_service


router = APIRouter(prefix="/fraud/ml", tags=["Fraud ML Models"])


class RegisterModelRequest(BaseModel):
    name: str
    model_type: ModelType
    algorithm: str
    created_by: str


class UpdateModelMetricsRequest(BaseModel):
    accuracy: Optional[float] = Field(None, ge=0, le=1)
    precision: Optional[float] = Field(None, ge=0, le=1)
    recall: Optional[float] = Field(None, ge=0, le=1)
    f1_score: Optional[float] = Field(None, ge=0, le=1)
    auc_roc: Optional[float] = Field(None, ge=0, le=1)


class PredictRequest(BaseModel):
    model_id: UUID
    input_data: Dict[str, Any]


class BatchPredictRequest(BaseModel):
    model_id: UUID
    input_data_list: List[Dict[str, Any]]


class StartTrainingRequest(BaseModel):
    model_id: UUID
    training_config: Dict[str, Any]
    created_by: str


class UpdateThresholdRequest(BaseModel):
    threshold: float = Field(ge=0, le=1)


@router.post("/models", response_model=MLModel)
async def register_model(request: RegisterModelRequest):
    """Register a new ML model"""
    model = await ml_service.register_model(
        name=request.name,
        model_type=request.model_type,
        algorithm=request.algorithm,
        created_by=request.created_by
    )
    return model


@router.get("/models/{model_id}", response_model=MLModel)
async def get_model(model_id: UUID):
    """Get ML model by ID"""
    model = await ml_service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("/models/{model_id}/activate", response_model=MLModel)
async def activate_model(model_id: UUID):
    """Activate an ML model"""
    model = await ml_service.activate_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.post("/models/{model_id}/deactivate", response_model=MLModel)
async def deactivate_model(model_id: UUID):
    """Deactivate an ML model"""
    model = await ml_service.deactivate_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.put("/models/{model_id}/metrics", response_model=MLModel)
async def update_model_metrics(model_id: UUID, request: UpdateModelMetricsRequest):
    """Update model performance metrics"""
    metrics = request.model_dump(exclude_none=True)
    model = await ml_service.update_model_metrics(model_id, metrics)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@router.put("/models/{model_id}/threshold", response_model=MLModel)
async def update_threshold(model_id: UUID, request: UpdateThresholdRequest):
    """Update model threshold"""
    model = await ml_service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    model.threshold = request.threshold
    return model


@router.get("/models", response_model=List[MLModel])
async def list_models(
    model_type: Optional[ModelType] = None,
    status: Optional[ModelStatus] = None,
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0)
):
    """List ML models with optional filters"""
    if status == ModelStatus.ACTIVE:
        models = await ml_service.get_active_models()
    else:
        # This would typically be handled by a repository method
        models = await ml_service.get_active_models()  # Simplified for demo
    return models[:limit]


@router.get("/models/active", response_model=List[MLModel])
async def get_active_models():
    """Get all active ML models"""
    return await ml_service.get_active_models()


@router.post("/predict", response_model=ModelPrediction)
async def predict(request: PredictRequest):
    """Make a prediction using an ML model"""
    prediction = await ml_service.predict(request.model_id, request.input_data)
    if not prediction:
        raise HTTPException(status_code=400, detail="Model not found or not active")
    return prediction


@router.post("/predict/batch")
async def batch_predict(request: BatchPredictRequest):
    """Make batch predictions using an ML model"""
    predictions = []
    for input_data in request.input_data_list:
        prediction = await ml_service.predict(request.model_id, input_data)
        if prediction:
            predictions.append(prediction)
    return {
        "model_id": str(request.model_id),
        "total_requests": len(request.input_data_list),
        "successful_predictions": len(predictions),
        "predictions": predictions
    }


@router.post("/training/start", response_model=ModelTrainingJob)
async def start_training(request: StartTrainingRequest):
    """Start a model training job"""
    job = await ml_service.start_training_job(
        model_id=request.model_id,
        training_config=request.training_config,
        created_by=request.created_by
    )
    return job


@router.get("/training/{job_id}", response_model=ModelTrainingJob)
async def get_training_job(job_id: UUID):
    """Get training job status"""
    job = await ml_service.get_training_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    return job


@router.get("/training")
async def list_training_jobs(
    model_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """List training jobs"""
    return {"training_jobs": []}


@router.post("/training/{job_id}/cancel")
async def cancel_training_job(job_id: UUID):
    """Cancel a training job"""
    job = await ml_service.get_training_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    job.status = "cancelled"
    return {"message": "Training job cancelled", "job_id": str(job_id)}


@router.get("/models/{model_id}/predictions")
async def get_model_predictions(
    model_id: UUID,
    limit: int = Query(default=100, le=500),
    fraud_only: bool = False
):
    """Get predictions made by a model"""
    return {"model_id": str(model_id), "predictions": []}


@router.get("/statistics/summary")
async def get_ml_statistics():
    """Get ML model statistics"""
    return await ml_service.get_statistics()
