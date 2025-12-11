"""Data Transformation Utilities"""

from typing import List, Dict, Any, Optional, Callable
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass
from uuid import uuid4


@dataclass
class TransformationStep:
    step_id: str
    step_name: str
    transformation_type: str
    source_fields: List[str]
    target_field: str
    parameters: Dict[str, Any]
    order: int


@dataclass
class TransformationPipeline:
    pipeline_id: str
    pipeline_name: str
    steps: List[TransformationStep]
    created_at: datetime
    is_active: bool = True


class DataTransformationUtilities:
    def __init__(self):
        self._pipelines: Dict[str, TransformationPipeline] = {}
        self._transformers: Dict[str, Callable] = {}
        self._register_default_transformers()

    def _register_default_transformers(self) -> None:
        self._transformers["concat"] = self._transform_concat
        self._transformers["split"] = self._transform_split
        self._transformers["map"] = self._transform_map
        self._transformers["calculate"] = self._transform_calculate
        self._transformers["aggregate"] = self._transform_aggregate
        self._transformers["pivot"] = self._transform_pivot
        self._transformers["unpivot"] = self._transform_unpivot
        self._transformers["filter"] = self._transform_filter
        self._transformers["sort"] = self._transform_sort
        self._transformers["deduplicate"] = self._transform_deduplicate

    def create_pipeline(
        self,
        pipeline_name: str,
        steps: List[Dict[str, Any]],
    ) -> TransformationPipeline:
        transformation_steps = []
        for i, step_config in enumerate(steps):
            step = TransformationStep(
                step_id=str(uuid4()),
                step_name=step_config.get("name", f"step_{i}"),
                transformation_type=step_config.get("type"),
                source_fields=step_config.get("source_fields", []),
                target_field=step_config.get("target_field", ""),
                parameters=step_config.get("parameters", {}),
                order=i,
            )
            transformation_steps.append(step)

        pipeline = TransformationPipeline(
            pipeline_id=str(uuid4()),
            pipeline_name=pipeline_name,
            steps=transformation_steps,
            created_at=datetime.utcnow(),
        )
        self._pipelines[pipeline.pipeline_id] = pipeline
        return pipeline

    def execute_pipeline(
        self,
        pipeline_id: str,
        data: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline or not pipeline.is_active:
            return data

        result = data.copy()
        for step in sorted(pipeline.steps, key=lambda s: s.order):
            transformer = self._transformers.get(step.transformation_type)
            if transformer:
                result = transformer(result, step)

        return result

    def transform_record(
        self,
        record: Dict[str, Any],
        transformations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        result = record.copy()

        for transform in transformations:
            transform_type = transform.get("type")
            source_fields = transform.get("source_fields", [])
            target_field = transform.get("target_field")
            params = transform.get("parameters", {})

            if transform_type == "concat":
                separator = params.get("separator", " ")
                values = [str(result.get(f, "")) for f in source_fields if result.get(f)]
                result[target_field] = separator.join(values)

            elif transform_type == "substring":
                source = result.get(source_fields[0], "") if source_fields else ""
                start = params.get("start", 0)
                length = params.get("length")
                if length:
                    result[target_field] = str(source)[start:start + length]
                else:
                    result[target_field] = str(source)[start:]

            elif transform_type == "replace":
                source = result.get(source_fields[0], "") if source_fields else ""
                old_value = params.get("old_value", "")
                new_value = params.get("new_value", "")
                result[target_field] = str(source).replace(old_value, new_value)

            elif transform_type == "upper":
                source = result.get(source_fields[0], "") if source_fields else ""
                result[target_field] = str(source).upper()

            elif transform_type == "lower":
                source = result.get(source_fields[0], "") if source_fields else ""
                result[target_field] = str(source).lower()

            elif transform_type == "trim":
                source = result.get(source_fields[0], "") if source_fields else ""
                result[target_field] = str(source).strip()

            elif transform_type == "coalesce":
                for field in source_fields:
                    value = result.get(field)
                    if value is not None and value != "":
                        result[target_field] = value
                        break

            elif transform_type == "default":
                source = result.get(source_fields[0]) if source_fields else None
                default_value = params.get("default_value")
                result[target_field] = source if source is not None else default_value

        return result

    def _transform_concat(
        self, data: List[Dict[str, Any]], step: TransformationStep
    ) -> List[Dict[str, Any]]:
        separator = step.parameters.get("separator", " ")
        result = []
        for record in data:
            new_record = record.copy()
            values = [str(record.get(f, "")) for f in step.source_fields if record.get(f)]
            new_record[step.target_field] = separator.join(values)
            result.append(new_record)
        return result

    def _transform_split(
        self, data: List[Dict[str, Any]], step: TransformationStep
    ) -> List[Dict[str, Any]]:
        delimiter = step.parameters.get("delimiter", ",")
        index = step.parameters.get("index", 0)
        source_field = step.source_fields[0] if step.source_fields else ""

        result = []
        for record in data:
            new_record = record.copy()
            value = str(record.get(source_field, ""))
            parts = value.split(delimiter)
            new_record[step.target_field] = parts[index] if index < len(parts) else ""
            result.append(new_record)
        return result

    def _transform_map(
        self, data: List[Dict[str, Any]], step: TransformationStep
    ) -> List[Dict[str, Any]]:
        mapping = step.parameters.get("mapping", {})
        default = step.parameters.get("default")
        source_field = step.source_fields[0] if step.source_fields else ""

        result = []
        for record in data:
            new_record = record.copy()
            value = record.get(source_field)
            new_record[step.target_field] = mapping.get(value, default)
            result.append(new_record)
        return result

    def _transform_calculate(
        self, data: List[Dict[str, Any]], step: TransformationStep
    ) -> List[Dict[str, Any]]:
        operation = step.parameters.get("operation", "add")

        result = []
        for record in data:
            new_record = record.copy()
            values = [float(record.get(f, 0)) for f in step.source_fields]

            if operation == "add":
                new_record[step.target_field] = sum(values)
            elif operation == "subtract" and len(values) >= 2:
                new_record[step.target_field] = values[0] - sum(values[1:])
            elif operation == "multiply":
                result_val = 1
                for v in values:
                    result_val *= v
                new_record[step.target_field] = result_val
            elif operation == "divide" and len(values) >= 2 and values[1] != 0:
                new_record[step.target_field] = values[0] / values[1]

            result.append(new_record)
        return result

    def _transform_aggregate(
        self, data: List[Dict[str, Any]], step: TransformationStep
    ) -> List[Dict[str, Any]]:
        return data

    def _transform_pivot(
        self, data: List[Dict[str, Any]], step: TransformationStep
    ) -> List[Dict[str, Any]]:
        return data

    def _transform_unpivot(
        self, data: List[Dict[str, Any]], step: TransformationStep
    ) -> List[Dict[str, Any]]:
        return data

    def _transform_filter(
        self, data: List[Dict[str, Any]], step: TransformationStep
    ) -> List[Dict[str, Any]]:
        conditions = step.parameters.get("conditions", [])
        result = []

        for record in data:
            include = True
            for condition in conditions:
                field = condition.get("field")
                operator = condition.get("operator", "eq")
                value = condition.get("value")
                record_value = record.get(field)

                if operator == "eq" and record_value != value:
                    include = False
                elif operator == "ne" and record_value == value:
                    include = False
                elif operator == "gt" and not (record_value > value):
                    include = False
                elif operator == "lt" and not (record_value < value):
                    include = False

            if include:
                result.append(record)

        return result

    def _transform_sort(
        self, data: List[Dict[str, Any]], step: TransformationStep
    ) -> List[Dict[str, Any]]:
        sort_field = step.source_fields[0] if step.source_fields else None
        descending = step.parameters.get("descending", False)

        if sort_field:
            return sorted(data, key=lambda x: x.get(sort_field, ""), reverse=descending)
        return data

    def _transform_deduplicate(
        self, data: List[Dict[str, Any]], step: TransformationStep
    ) -> List[Dict[str, Any]]:
        key_fields = step.source_fields
        seen = set()
        result = []

        for record in data:
            key = tuple(str(record.get(f, "")) for f in key_fields)
            if key not in seen:
                seen.add(key)
                result.append(record)

        return result

    def register_transformer(self, name: str, func: Callable) -> None:
        self._transformers[name] = func

    def get_available_transformers(self) -> List[str]:
        return list(self._transformers.keys())


data_transformation_utilities = DataTransformationUtilities()
