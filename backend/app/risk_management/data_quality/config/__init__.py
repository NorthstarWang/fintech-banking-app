"""Data Quality Configuration"""

from .quality_thresholds import QualityThresholds, quality_thresholds
from .dimension_weights import DimensionWeights, dimension_weights
from .validation_config import ValidationConfig, validation_config
from .profiling_config import ProfilingConfig, profiling_config
from .mdm_config import MDMConfig, mdm_config

__all__ = [
    "QualityThresholds",
    "quality_thresholds",
    "DimensionWeights",
    "dimension_weights",
    "ValidationConfig",
    "validation_config",
    "ProfilingConfig",
    "profiling_config",
    "MDMConfig",
    "mdm_config",
]
