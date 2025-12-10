"""
Redis-based queue for task events.
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime
from common.cache.redis_client import get_redis_client, is_redis_available
import logging

logger = logging.getLogger(__name__)

class RedisEventQueue:
    """Redis-based event queue for task notifications."""
    
    def __init__(self):
        self.queue_name = "task-events-queue"
    
    def _get_client(self):
        """Get Redis client. Initializes Redis if not already initialized."""
        redis_client = get_redis_client()  # This will initialize if needed
        if not is_redis_available():
            logger.warning("Redis not available after initialization attempt")
            return None
        return redis_client
    
    def enqueue_task_event(
        self,
        event_type: str,  # "task_created", "task_updated", "task_deleted"
        task_id: int,
        task_title: str,
        assigned_to_id: Optional[int] = None,
        reporting_to_id: Optional[int] = None,
        assigned_to_email: Optional[str] = None,
        reporting_to_email: Optional[str] = None,
        updated_by_id: Optional[int] = None,
        updated_by_email: Optional[str] = None,
        updated_by_role: Optional[str] = None,
        organization_id: Optional[int] = None,
        organization_name: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        reason: Optional[str] = None
    ):
        """Add task event to queue for email notifications."""
        redis_client = self._get_client()
        if not redis_client:
            logger.warning("Redis not available, skipping event queue")
            return
        
        event = {
            "event_type": event_type,
            "task_id": task_id,
            "task_title": task_title,
            "assigned_to_id": assigned_to_id,
            "reporting_to_id": reporting_to_id,
            "assigned_to_email": assigned_to_email,
            "reporting_to_email": reporting_to_email,
            "updated_by_id": updated_by_id,
            "updated_by_email": updated_by_email,
            "updated_by_role": updated_by_role,
            "organization_id": organization_id,
            "organization_name": organization_name,
            "changes": changes or {},
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Push to right side of list (FIFO queue)
            redis_client.rpush(self.queue_name, json.dumps(event))
            logger.info(f"Enqueued {event_type} event for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to enqueue task event: {str(e)}")
            # Don't fail task operation if queue fails

# Singleton instance
redis_queue = RedisEventQueue()

