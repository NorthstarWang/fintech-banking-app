"""
Machine Learning Models

Defines data structures for ML-based fraud detection.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class ModelType(str, Enum):
    CLASSIFICATION = "classification"
    ANOMALY_DETECTION = "anomaly_detection"
    CLUSTERING = "clustering"
    SEQUENCE = "sequence"
    ENSEMBLE = "ensemble"


class ModelStatus(str, Enum):
    TRAINING = "training"
    VALIDATING = "validating"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"
    FAILED = "failed"


class MLModel(BaseModel):
    model_id: UUID = Field(default_factory=uuid4)
    model_name: str
    model_type: ModelType
    model_version: str

    status: ModelStatus = ModelStatus.TRAINING

    description: str
    algorithm: str
    framework: str

    features: List[str] = Field(default_factory=list)
    target_variable: Optional[str] = None

    hyperparameters: Dict[str, Any] = Field(default_factory=dict)

    training_data_start: Optional[datetime] = None
    training_data_end: Optional[datetime] = None
    training_samples: int = 0

    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    auc_roc: float = 0.0

    threshold: float = 0.5

    model_path: Optional[str] = None
    model_size_mb: float = 0.0

    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    trained_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None

    metadata: Dict[str, Any] = Field(default_factory=dict)


class ModelPrediction(BaseModel):
    prediction_id: UUID = Field(default_factory=uuid4)
    model_id: UUID

    input_data: Dict[str, Any]

    prediction: Any
    probability: float = 0.0
    confidence: float = 0.0

    features_used: Dict[str, Any] = Field(default_factory=dict)
    feature_importance: Dict[str, float] = Field(default_factory=dict)

    predicted_at: datetime = Field(default_factory=datetime.utcnow)
    prediction_time_ms: float = 0.0

    is_fraud: bool = False
    fraud_score: float = 0.0


class ModelTrainingJob(BaseModel):
    job_id: UUID = Field(default_factory=uuid4)
    model_id: UUID

    status: str = "pending"

    training_config: Dict[str, Any] = Field(default_factory=dict)

    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    epochs_completed: int = 0
    total_epochs: int = 0
    current_loss: float = 0.0
    current_accuracy: float = 0.0

    error_message: Optional[str] = None

    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ModelPerformanceMetrics(BaseModel):
    metrics_id: UUID = Field(default_factory=uuid4)
    model_id: UUID

    period_start: datetime
    period_end: datetime

    total_predictions: int = 0
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0

    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0

    average_prediction_time_ms: float = 0.0

    drift_score: float = 0.0
    needs_retraining: bool = False

    calculated_at: datetime = Field(default_factory=datetime.utcnow)


class FeatureStore(BaseModel):
    feature_id: UUID = Field(default_factory=uuid4)
    feature_name: str
    feature_type: str

    description: str
    calculation_logic: str

    source_tables: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)

    refresh_frequency: str = "daily"
    last_refresh: Optional[datetime] = None

    is_active: bool = True

    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MLModelStatistics(BaseModel):
    total_models: int = 0
    active_models: int = 0
    by_type: Dict[str, int] = Field(default_factory=dict)
    total_predictions_today: int = 0
    average_accuracy: float = 0.0
    models_requiring_retraining: int = 0
