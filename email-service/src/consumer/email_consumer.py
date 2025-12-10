"""
Email service worker that consumes from Redis queue.
"""
import json
import time
import logging
from typing import Dict, Any, Optional
from common.cache.redis_client import get_redis_client, is_redis_available, initialize_redis
from common.config.settings import settings
from src.email.email_sender import send_task_notification_email

# Import redis for exception handling
try:
    import redis
except ImportError:
    redis = None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailWorker:
    """Worker that processes email events from Redis queue."""
    
    def __init__(self):
        self.queue_name = settings.QUEUE_NAME
        self.blocking_timeout = settings.QUEUE_BLOCKING_TIMEOUT
        self.running = False
    
    def start(self):
        """Start consuming from queue."""
        # Initialize Redis
        if not initialize_redis():
            logger.error("❌ Failed to initialize Redis. Exiting.")
            return
        
        if not is_redis_available():
            logger.error("❌ Redis not available. Exiting.")
            return
        
        self.running = True
        logger.info(f"📧 Email worker started, listening on queue: {self.queue_name}")
        logger.info(f"⏱️  Blocking timeout: {self.blocking_timeout} seconds")
        
        redis_client = get_redis_client()
        
        while self.running:
            try:
                # Blocking pop from left side (FIFO)
                # BLPOP blocks until data arrives or timeout
                result = redis_client.blpop(self.queue_name, timeout=self.blocking_timeout)
                
                if result:
                    queue_name, event_json = result
                    event = json.loads(event_json)
                    self.process_event(event)
                else:
                    # Timeout - no data available, continue waiting
                    # This is normal, not an error
                    continue
                    
            except KeyboardInterrupt:
                logger.info("🛑 Stopping email worker...")
                self.running = False
                break
            except Exception as e:
                error_str = str(e).lower()
                # Handle Redis-specific errors
                if redis:
                    if isinstance(e, redis.exceptions.TimeoutError):
                        # Socket timeout - reconnect and retry
                        logger.warning("⚠️  Redis timeout, reconnecting...")
                        if not initialize_redis():
                            logger.error("❌ Failed to reconnect to Redis")
                            time.sleep(5)
                        else:
                            redis_client = get_redis_client()
                        continue
                    elif isinstance(e, redis.exceptions.ConnectionError):
                        logger.error(f"❌ Redis connection error: {str(e)}")
                        logger.info("🔄 Attempting to reconnect in 5 seconds...")
                        time.sleep(5)
                        if initialize_redis():
                            redis_client = get_redis_client()
                        continue
                
                # Handle generic timeout/connection errors
                if 'timeout' in error_str or 'connection' in error_str:
                    logger.warning(f"⚠️  Connection issue: {str(e)}, retrying...")
                    time.sleep(2)
                    if initialize_redis():
                        redis_client = get_redis_client()
                    continue
                
                # Other errors
                logger.error(f"❌ Unexpected error: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                time.sleep(1)  # Wait before retrying
        
        logger.info("✅ Email worker stopped")
    
    def process_event(self, event: Dict[str, Any]):
        """Process a task event and send emails."""
        try:
            event_type = event.get('event_type')
            task_id = event.get('task_id')
            task_title = event.get('task_title')
            assigned_to_email = event.get('assigned_to_email')
            reporting_to_email = event.get('reporting_to_email')
            updated_by_id = event.get('updated_by_id')
            updated_by_email = event.get('updated_by_email')
            updated_by_role = event.get('updated_by_role', 'Owner')
            organization_name = event.get('organization_name')
            changes = event.get('changes', {})
            reason = event.get('reason')
            
            logger.info(f"📬 Processing {event_type} event for task {task_id}")
            
            # Send email to assigned developer
            if assigned_to_email:
                send_task_notification_email(
                    to_email=assigned_to_email,
                    event_type=event_type,
                    task_id=task_id,
                    task_title=task_title,
                    updated_by_email=updated_by_email,
                    updated_by_role=updated_by_role,
                    organization_name=organization_name,
                    changes=changes,
                    reason=reason,
                    recipient_type="assigned_to"
                )
            else:
                logger.warning(f"⚠️  No assigned_to_email for task {task_id}")
            
            # Send email to reporting product owner
            if reporting_to_email:
                send_task_notification_email(
                    to_email=reporting_to_email,
                    event_type=event_type,
                    task_id=task_id,
                    task_title=task_title,
                    updated_by_email=updated_by_email,
                    updated_by_role=updated_by_role,
                    organization_name=organization_name,
                    changes=changes,
                    reason=reason,
                    recipient_type="reporting_to"
                )
            else:
                logger.warning(f"⚠️  No reporting_to_email for task {task_id}")
            
            logger.info(f"✅ Processed {event_type} event for task {task_id}")
            
        except Exception as e:
            logger.error(f"❌ Error processing email event: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())


if __name__ == "__main__":
    worker = EmailWorker()
    worker.start()

