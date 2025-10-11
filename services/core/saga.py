"""Saga pattern for distributed transactions across microservices."""
import logging
import uuid
from enum import Enum
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class SagaStepStatus(Enum):
    """Status of a saga step."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


@dataclass
class SagaStep:
    """Represents a step in a saga."""
    name: str
    action: Callable
    compensation: Optional[Callable] = None
    retry_count: int = 0
    max_retries: int = 3
    status: SagaStepStatus = SagaStepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    async def execute(self) -> bool:
        """Execute the saga step."""
        self.status = SagaStepStatus.EXECUTING
        self.started_at = datetime.utcnow()

        try:
            self.result = await self.action()
            self.status = SagaStepStatus.COMPLETED
            self.completed_at = datetime.utcnow()
            logger.info(f"Saga step '{self.name}' completed successfully")
            return True

        except Exception as e:
            self.error = str(e)
            logger.error(f"Saga step '{self.name}' failed: {e}")

            if self.retry_count < self.max_retries:
                self.retry_count += 1
                logger.info(f"Retrying saga step '{self.name}' (attempt {self.retry_count}/{self.max_retries})")
                await asyncio.sleep(2 ** self.retry_count)  # Exponential backoff
                return await self.execute()

            self.status = SagaStepStatus.FAILED
            return False

    async def compensate(self) -> bool:
        """Execute compensation (rollback) for this step."""
        if not self.compensation:
            logger.debug(f"No compensation defined for saga step '{self.name}'")
            return True

        self.status = SagaStepStatus.COMPENSATING

        try:
            await self.compensation(self.result)
            self.status = SagaStepStatus.COMPENSATED
            self.completed_at = datetime.utcnow()
            logger.info(f"Saga step '{self.name}' compensated successfully")
            return True

        except Exception as e:
            logger.error(f"Compensation for saga step '{self.name}' failed: {e}")
            self.error = f"Compensation failed: {e}"
            return False


class SagaStatus(Enum):
    """Overall saga status."""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"


class Saga:
    """
    Implements the Saga pattern for distributed transactions.

    Saga is a sequence of local transactions coordinated through event messaging.
    If one step fails, previous steps are compensated in reverse order.
    """

    def __init__(self, saga_id: str = None):
        self.saga_id = saga_id or str(uuid.uuid4())
        self.steps: List[SagaStep] = []
        self.status = SagaStatus.PENDING
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.last_error: Optional[str] = None

    def add_step(
        self,
        name: str,
        action: Callable,
        compensation: Optional[Callable] = None,
        max_retries: int = 3
    ) -> SagaStep:
        """Add a step to the saga."""
        step = SagaStep(
            name=name,
            action=action,
            compensation=compensation,
            max_retries=max_retries
        )
        self.steps.append(step)
        logger.info(f"Added step '{name}' to saga {self.saga_id}")
        return step

    async def execute(self) -> bool:
        """
        Execute the saga.

        Returns:
            True if all steps completed, False if compensated due to failure
        """
        self.status = SagaStatus.EXECUTING
        self.started_at = datetime.utcnow()

        completed_steps: List[SagaStep] = []

        try:
            # Execute all steps in order
            for step in self.steps:
                logger.info(f"Executing saga step '{step.name}'")
                success = await step.execute()

                if not success:
                    self.status = SagaStatus.FAILED
                    self.last_error = step.error
                    logger.error(f"Saga {self.saga_id} failed at step '{step.name}'")

                    # Compensate previous steps in reverse order
                    await self._compensate(completed_steps)
                    return False

                completed_steps.append(step)

            # All steps completed successfully
            self.status = SagaStatus.COMPLETED
            self.completed_at = datetime.utcnow()
            logger.info(f"Saga {self.saga_id} completed successfully")
            return True

        except Exception as e:
            logger.error(f"Unexpected error in saga {self.saga_id}: {e}")
            self.last_error = str(e)
            self.status = SagaStatus.FAILED

            # Compensate previous steps
            await self._compensate(completed_steps)
            return False

    async def _compensate(self, steps: List[SagaStep]):
        """Compensate steps in reverse order."""
        self.status = SagaStatus.COMPENSATING
        logger.info(f"Starting compensation for saga {self.saga_id}")

        # Compensate in reverse order
        for step in reversed(steps):
            logger.info(f"Compensating saga step '{step.name}'")
            await step.compensate()

        self.status = SagaStatus.COMPENSATED
        self.completed_at = datetime.utcnow()
        logger.info(f"Saga {self.saga_id} compensated")

    def get_status(self) -> Dict[str, Any]:
        """Get saga execution status."""
        return {
            "saga_id": self.saga_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_error": self.last_error,
            "steps": [
                {
                    "name": step.name,
                    "status": step.status.value,
                    "result": str(step.result) if step.result else None,
                    "error": step.error,
                    "retry_count": step.retry_count,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None
                }
                for step in self.steps
            ]
        }


class SagaOrchestrator:
    """Manages multiple sagas."""

    def __init__(self):
        self.sagas: Dict[str, Saga] = {}

    def create_saga(self, saga_id: str = None) -> Saga:
        """Create a new saga."""
        saga = Saga(saga_id)
        self.sagas[saga.saga_id] = saga
        return saga

    async def execute_saga(self, saga: Saga) -> bool:
        """Execute a saga and track it."""
        success = await saga.execute()
        logger.info(
            f"Saga {saga.saga_id} {'completed' if success else 'failed'}",
            extra={"saga_status": saga.get_status()}
        )
        return success

    def get_saga(self, saga_id: str) -> Optional[Saga]:
        """Get saga by ID."""
        return self.sagas.get(saga_id)

    def get_all_sagas(self) -> List[Dict[str, Any]]:
        """Get all sagas."""
        return [saga.get_status() for saga in self.sagas.values()]

    def get_failed_sagas(self) -> List[Dict[str, Any]]:
        """Get all failed sagas."""
        return [
            saga.get_status()
            for saga in self.sagas.values()
            if saga.status == SagaStatus.FAILED
        ]


# Global saga orchestrator
_orchestrator: Optional[SagaOrchestrator] = None


def get_saga_orchestrator() -> SagaOrchestrator:
    """Get or create global saga orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SagaOrchestrator()
    return _orchestrator


def init_saga_orchestrator() -> SagaOrchestrator:
    """Initialize global saga orchestrator."""
    global _orchestrator
    _orchestrator = SagaOrchestrator()
    return _orchestrator
