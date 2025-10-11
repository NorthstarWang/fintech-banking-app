"""In-memory service discovery registry for service-to-service communication."""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class ServiceInstance:
    """Represents a service instance in the registry."""
    service_name: str
    instance_id: str
    host: str
    port: int
    health_check_url: str
    api_key: str
    is_healthy: bool = True
    last_heartbeat: datetime = None
    metadata: Dict = None

    def __post_init__(self):
        if self.last_heartbeat is None:
            self.last_heartbeat = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}

    @property
    def base_url(self) -> str:
        """Get base URL for the service instance."""
        return f"http://{self.host}:{self.port}"


class ServiceRegistry:
    """In-memory service registry with health checking."""

    def __init__(self, heartbeat_timeout: int = 30):
        self._services: Dict[str, List[ServiceInstance]] = {}
        self._heartbeat_timeout = timedelta(seconds=heartbeat_timeout)
        self._lock = threading.RLock()

    def register(
        self,
        service_name: str,
        instance_id: str,
        host: str,
        port: int,
        health_check_url: str,
        api_key: str,
        metadata: Optional[Dict] = None
    ) -> ServiceInstance:
        """Register a new service instance."""
        with self._lock:
            instance = ServiceInstance(
                service_name=service_name,
                instance_id=instance_id,
                host=host,
                port=port,
                health_check_url=health_check_url,
                api_key=api_key,
                metadata=metadata or {}
            )

            if service_name not in self._services:
                self._services[service_name] = []

            # Check if instance already exists and remove it
            self._services[service_name] = [
                s for s in self._services[service_name]
                if s.instance_id != instance_id
            ]

            self._services[service_name].append(instance)
            logger.info(f"Registered service: {service_name}/{instance_id} at {host}:{port}")
            return instance

    def deregister(self, service_name: str, instance_id: str) -> bool:
        """Deregister a service instance."""
        with self._lock:
            if service_name in self._services:
                before_count = len(self._services[service_name])
                self._services[service_name] = [
                    s for s in self._services[service_name]
                    if s.instance_id != instance_id
                ]
                if len(self._services[service_name]) < before_count:
                    logger.info(f"Deregistered service: {service_name}/{instance_id}")
                    return True
            return False

    def get_instance(
        self,
        service_name: str,
        load_balanced: bool = True
    ) -> Optional[ServiceInstance]:
        """Get a service instance, with optional load balancing."""
        with self._lock:
            instances = self._services.get(service_name, [])
            healthy_instances = [s for s in instances if s.is_healthy]

            if not healthy_instances:
                logger.warning(f"No healthy instances for service: {service_name}")
                return None

            if load_balanced:
                # Simple round-robin would require additional state
                # For now, return first healthy instance
                return healthy_instances[0]

            return healthy_instances[0]

    def get_all_instances(self, service_name: str) -> List[ServiceInstance]:
        """Get all instances of a service."""
        with self._lock:
            return self._services.get(service_name, []).copy()

    def heartbeat(self, service_name: str, instance_id: str) -> bool:
        """Update heartbeat for a service instance."""
        with self._lock:
            if service_name in self._services:
                for instance in self._services[service_name]:
                    if instance.instance_id == instance_id:
                        instance.last_heartbeat = datetime.utcnow()
                        instance.is_healthy = True
                        return True
            return False

    def mark_unhealthy(self, service_name: str, instance_id: str) -> bool:
        """Mark a service instance as unhealthy."""
        with self._lock:
            if service_name in self._services:
                for instance in self._services[service_name]:
                    if instance.instance_id == instance_id:
                        instance.is_healthy = False
                        logger.warning(f"Marked unhealthy: {service_name}/{instance_id}")
                        return True
            return False

    def check_stale_instances(self):
        """Remove instances that haven't sent heartbeat within timeout."""
        with self._lock:
            now = datetime.utcnow()
            removed = []

            for service_name, instances in self._services.items():
                before_count = len(instances)
                self._services[service_name] = [
                    s for s in instances
                    if (now - s.last_heartbeat) < self._heartbeat_timeout
                ]
                removed_count = before_count - len(self._services[service_name])
                if removed_count > 0:
                    removed.append((service_name, removed_count))

            if removed:
                logger.info(f"Removed stale instances: {removed}")

    def get_registry_status(self) -> Dict:
        """Get current registry status."""
        with self._lock:
            status = {}
            for service_name, instances in self._services.items():
                status[service_name] = {
                    "total_instances": len(instances),
                    "healthy_instances": len([s for s in instances if s.is_healthy]),
                    "instances": [
                        {
                            "instance_id": s.instance_id,
                            "url": s.base_url,
                            "is_healthy": s.is_healthy,
                            "last_heartbeat": s.last_heartbeat.isoformat()
                        }
                        for s in instances
                    ]
                }
            return status


# Global registry instance
_registry: Optional[ServiceRegistry] = None


def get_registry() -> ServiceRegistry:
    """Get or create the global service registry."""
    global _registry
    if _registry is None:
        _registry = ServiceRegistry()
    return _registry


def init_registry(heartbeat_timeout: int = 30) -> ServiceRegistry:
    """Initialize the global service registry."""
    global _registry
    _registry = ServiceRegistry(heartbeat_timeout=heartbeat_timeout)
    return _registry
