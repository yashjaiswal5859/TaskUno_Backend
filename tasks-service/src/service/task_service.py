"""
Service layer for task business logic.
"""
from typing import List, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.models import Task, TaskLog
from src.repository.task_repository import TaskRepository, Project
from src.schemas import TaskBase, TaskUpdate
from common.client.http_client import create_service_client
from common.config.settings import settings
from common.database.audit_service import log_audit
from common.messaging.redis_queue import redis_queue

organization_client = create_service_client(settings.ORGANIZATION_SERVICE_URL)


class TaskService:
    """Service for task operations."""

    def __init__(self, db: Session):
        self.repository = TaskRepository(db)
        self.db = db

    async def create_task(self, task_data: TaskBase, employee_id: int, role_type: str, organization_id: int, token: str) -> Task:
        """Create a new task."""
        # Verify project belongs to organization
        project = self.db.query(Project).filter(Project.id == task_data.project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        if project.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Project does not belong to your organization"
            )
        
        # Verify developer belongs to organization (via Organization Service) - REQUIRED
        try:
            headers = {"Authorization": f"Bearer {token}"}
            developers = await organization_client.get("/organization/developers", headers=headers)
            dev_found = any(d['id'] == task_data.assigned_to for d in developers)
            if not dev_found:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Developer not found in your organization"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying developer: {str(e)}"
            )
        
        # Verify reporting_to (Product Owner) belongs to organization - REQUIRED
        reporting_to_id = task_data.reporting_to
        try:
            headers = {"Authorization": f"Bearer {token}"}
            product_owners = await organization_client.get("/organization/product-owners", headers=headers)
            po_found = any(po['id'] == reporting_to_id for po in product_owners)
            if not po_found:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product Owner not found in your organization"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error verifying product owner: {str(e)}"
            )
        
        task_dict = {
            "title": task_data.title,
            "description": task_data.description,
            "status": task_data.status,
            "project_id": task_data.project_id,
            "createdDate": datetime.now(),
            "dueDate": task_data.dueDate,
            "assigned_to": task_data.assigned_to,
            "reporting_to": reporting_to_id
        }
        new_task = self.repository.create(task_dict)
        
        # Log audit entry - Product Owner created task with task ID
        log_audit(
            db=self.db,
            employee_id=employee_id,
            role_type=role_type,
            action="task_created",
            organization_id=organization_id,
            resource_type="task",
            resource_id=new_task.id,
            details={
                "message": f"Product Owner created task with id: {new_task.id}",
                "title": task_data.title,
                "status": task_data.status,
                "project_id": task_data.project_id,
                "assigned_to": task_data.assigned_to,
                "reporting_to": reporting_to_id
            }
        )
        
        # Enqueue task created event for email notifications
        try:
            # Get email addresses
            assigned_to_email = None
            reporting_to_email = None
            updated_by_email = None
            organization_name = None
            
            # Get updated_by email
            if employee_id and token:
                try:
                    headers = {"Authorization": f"Bearer {token}"}
                    # Try to get from developers first
                    developers = await organization_client.get("/organization/developers", headers=headers)
                    dev = next((d for d in developers if d['id'] == employee_id), None)
                    if dev:
                        updated_by_email = dev.get('email')
                    else:
                        # Try product owners
                        product_owners = await organization_client.get("/organization/product-owners", headers=headers)
                        po = next((p for p in product_owners if p['id'] == employee_id), None)
                        if po:
                            updated_by_email = po.get('email')
                except Exception as e:
                    print(f"[WARNING] Failed to get updated_by email: {str(e)}")
            
            # Get organization name
            if organization_id and token:
                try:
                    headers = {"Authorization": f"Bearer {token}"}
                    org_info = await organization_client.get(f"/organization/{organization_id}", headers=headers)
                    if org_info:
                        organization_name = org_info.get('name') or org_info.get('title')
                except Exception as e:
                    print(f"[WARNING] Failed to get organization name: {str(e)}")
            
            if new_task.assigned_to and token:
                try:
                    headers = {"Authorization": f"Bearer {token}"}
                    developers = await organization_client.get("/organization/developers", headers=headers)
                    dev = next((d for d in developers if d['id'] == new_task.assigned_to), None)
                    if dev:
                        assigned_to_email = dev.get('email')
                except Exception as e:
                    print(f"[WARNING] Failed to get assigned_to email: {str(e)}")
            
            if new_task.reporting_to and token:
                try:
                    headers = {"Authorization": f"Bearer {token}"}
                    product_owners = await organization_client.get("/organization/product-owners", headers=headers)
                    po = next((p for p in product_owners if p['id'] == new_task.reporting_to), None)
                    if po:
                        reporting_to_email = po.get('email')
                except Exception as e:
                    print(f"[WARNING] Failed to get reporting_to email: {str(e)}")
            
            # Enqueue to Redis
            redis_queue.enqueue_task_event(
                event_type="task_created",
                task_id=new_task.id,
                task_title=new_task.title,
                assigned_to_id=new_task.assigned_to,
                reporting_to_id=new_task.reporting_to,
                assigned_to_email=assigned_to_email,
                reporting_to_email=reporting_to_email,
                updated_by_id=employee_id,
                updated_by_email=updated_by_email,
                updated_by_role=role_type,
                organization_id=organization_id,
                organization_name=organization_name
            )
        except Exception as e:
            print(f"[ERROR] Failed to enqueue task created event: {str(e)}")
        
        return new_task

    def get_task_by_id(self, task_id: int, organization_id: int) -> Task:
        """Get task by ID."""
        task = self.repository.get_by_id_with_org_check(task_id, organization_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task Not Found!"
            )
        return task

    def get_all_tasks(self, organization_id: int) -> List[Task]:
        """Get all tasks for an organization."""
        return self.repository.get_all_by_organization_id(organization_id)

    async def update_task(self, task_id: int, update_data: TaskUpdate, user_role: str, user_id: int, organization_id: int, token: str = None) -> Task:
        """Update task."""
        task = self.repository.get_by_id_with_org_check(task_id, organization_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        old_status = task.status
        # Extract status_change_reason first before dumping
        reason = getattr(update_data, 'status_change_reason', None)
        # If reason is not provided, set default based on user role
        if not reason:
            if user_role == "Product Owner":
                reason = "Product Owner modified task"
            elif user_role == "Developer":
                reason = "Developer modified task"
            else:
                reason = "Owner modified task"
        
        # Dump the update data
        update_dict = update_data.model_dump(exclude_unset=True, exclude_none=True)
        # Remove status_change_reason from update_dict as it's not a database field
        update_dict.pop('status_change_reason', None)
        new_status = update_dict.get('status', old_status)
        
        # Debug: print what we're updating
        print(f"[DEBUG] Updating task {task_id} with: {update_dict}")
        
        # Developers can only update status field - restrict before processing other fields
        if user_role == "Developer":
            # Check if any field other than 'status' is being updated
            allowed_fields = {'status'}
            update_fields = set(update_dict.keys())
            # Reject if trying to update any field other than status
            if not update_fields.issubset(allowed_fields):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Developers can only update the status field"
                )
            # Ensure status is being updated (not just other fields)
            if 'status' not in update_dict:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Developers can only update the status field"
                )
            # For Developers, only keep status in update_dict (remove any other fields)
            update_dict = {'status': update_dict.get('status', old_status)}
        
        # Convert dueDate from date to datetime if present (only for Product Owners)
        # Pydantic converts the string to a date object, so we need to convert date to datetime
        if 'dueDate' in update_dict and update_dict['dueDate'] is not None:
            try:
                due_date_value = update_dict['dueDate']
                if isinstance(due_date_value, date) and not isinstance(due_date_value, datetime):
                    # Convert date to datetime (set to midnight)
                    update_dict['dueDate'] = datetime.combine(due_date_value, datetime.min.time())
                elif isinstance(due_date_value, str):
                    # If it's still a string, parse it first
                    from datetime import datetime as dt
                    parsed_date = dt.strptime(due_date_value, '%Y-%m-%d').date()
                    update_dict['dueDate'] = datetime.combine(parsed_date, datetime.min.time())
                elif isinstance(due_date_value, datetime):
                    # If it's already a datetime, leave it as is
                    pass
                else:
                    # Unknown type, try to convert
                    raise ValueError(f"Unexpected type for dueDate: {type(due_date_value)}")
            except (ValueError, TypeError) as e:
                import traceback
                error_detail = f"Invalid date format for dueDate: {update_dict.get('dueDate')}. Expected YYYY-MM-DD. Error: {str(e)}\n{traceback.format_exc()}"
                print(f"[ERROR] {error_detail}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format for dueDate: {update_dict.get('dueDate')}. Expected YYYY-MM-DD. Error: {str(e)}"
                )
        
        # Validate assigned_to if being updated
        if 'assigned_to' in update_dict and update_dict['assigned_to'] is not None:
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token required to validate assigned_to"
                )
            try:
                headers = {"Authorization": f"Bearer {token}"}
                developers = await organization_client.get("/organization/developers", headers=headers)
                dev_found = any(d['id'] == update_dict['assigned_to'] for d in developers)
                if not dev_found:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Developer not found in your organization"
                    )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error verifying developer: {str(e)}"
                )
        
        # Validate reporting_to if being updated
        if 'reporting_to' in update_dict and update_dict['reporting_to'] is not None:
            if not token:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Token required to validate reporting_to"
                )
            try:
                headers = {"Authorization": f"Bearer {token}"}
                product_owners = await organization_client.get("/organization/product-owners", headers=headers)
                po_found = any(po['id'] == update_dict['reporting_to'] for po in product_owners)
                if not po_found:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Product Owner not found in your organization"
                    )
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error verifying product owner: {str(e)}"
                )
        
        try:
            updated_task = self.repository.update(task, update_dict)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating task in database: {str(e)}"
            )
        
        # Create task log entry if status changed
        if old_status != new_status:
            self.repository.create_log(
                task_id=task_id,
                reason=reason,
                old_status=old_status,
                new_status=new_status
            )
        
        # Log audit entry
        log_audit(
            db=self.db,
            employee_id=user_id,
            role_type=user_role,
            action="task_updated",
            organization_id=organization_id,
            resource_type="task",
            resource_id=task_id,
            details={
                "changes": update_dict,
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason
            }
        )
        
        # Enqueue task updated event for email notifications
        try:
            # Get email addresses
            assigned_to_email = None
            reporting_to_email = None
            updated_by_email = None
            organization_name = None
            
            # Get updated_by email
            if user_id and token:
                try:
                    headers = {"Authorization": f"Bearer {token}"}
                    # Try to get from developers first
                    developers = await organization_client.get("/organization/developers", headers=headers)
                    dev = next((d for d in developers if d['id'] == user_id), None)
                    if dev:
                        updated_by_email = dev.get('email')
                    else:
                        # Try product owners
                        product_owners = await organization_client.get("/organization/product-owners", headers=headers)
                        po = next((p for p in product_owners if p['id'] == user_id), None)
                        if po:
                            updated_by_email = po.get('email')
                except Exception as e:
                    print(f"[WARNING] Failed to get updated_by email: {str(e)}")
            
            # Get organization name
            if organization_id and token:
                try:
                    headers = {"Authorization": f"Bearer {token}"}
                    org_info = await organization_client.get(f"/organization/{organization_id}", headers=headers)
                    if org_info:
                        organization_name = org_info.get('name') or org_info.get('title')
                except Exception as e:
                    print(f"[WARNING] Failed to get organization name: {str(e)}")
            
            if updated_task.assigned_to and token:
                try:
                    headers = {"Authorization": f"Bearer {token}"}
                    developers = await organization_client.get("/organization/developers", headers=headers)
                    dev = next((d for d in developers if d['id'] == updated_task.assigned_to), None)
                    if dev:
                        assigned_to_email = dev.get('email')
                except Exception as e:
                    print(f"[WARNING] Failed to get assigned_to email: {str(e)}")
            
            if updated_task.reporting_to and token:
                try:
                    headers = {"Authorization": f"Bearer {token}"}
                    product_owners = await organization_client.get("/organization/product-owners", headers=headers)
                    po = next((p for p in product_owners if p['id'] == updated_task.reporting_to), None)
                    if po:
                        reporting_to_email = po.get('email')
                except Exception as e:
                    print(f"[WARNING] Failed to get reporting_to email: {str(e)}")
            
            # Format changes with old/new values for status
            formatted_changes = {}
            for key, new_value in update_dict.items():
                if key == 'status' and old_status != new_status:
                    # Format status change with old → new
                    formatted_changes[key] = {
                        'old': old_status,
                        'new': new_value
                    }
                else:
                    # For other fields, just include the new value
                    formatted_changes[key] = new_value
            
            # Enqueue to Redis
            redis_queue.enqueue_task_event(
                event_type="task_updated",
                task_id=updated_task.id,
                task_title=updated_task.title,
                assigned_to_id=updated_task.assigned_to,
                reporting_to_id=updated_task.reporting_to,
                assigned_to_email=assigned_to_email,
                reporting_to_email=reporting_to_email,
                updated_by_id=user_id,
                updated_by_email=updated_by_email,
                updated_by_role=user_role,
                organization_id=organization_id,
                organization_name=organization_name,
                changes=formatted_changes,
                reason=reason
            )
        except Exception as e:
            print(f"[ERROR] Failed to enqueue task updated event: {str(e)}")
        
        return updated_task

    def delete_task(self, task_id: int, user_id: int, user_role: str, organization_id: int) -> None:
        """Delete a task."""
        task = self.repository.get_by_id_with_org_check(task_id, organization_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
        
        # Get email addresses before deletion (task will be deleted)
        assigned_to_email = None
        reporting_to_email = None
        
        # Try to get emails (we'll need to call organization service, but we don't have token here)
        # For now, we'll enqueue with IDs and let email service fetch emails
        
        # Log audit entry before deletion
        log_audit(
            db=self.db,
            employee_id=user_id,
            role_type=user_role,
            action="task_deleted",
            organization_id=organization_id,
            resource_type="task",
            resource_id=task_id,
            details={
                "title": task.title,
                "status": task.status
            }
        )
        
        # Enqueue task deleted event for email notifications (before deletion)
        try:
            # Get email addresses and organization info
            assigned_to_email = None
            reporting_to_email = None
            updated_by_email = None
            organization_name = None
            
            # Note: For delete, we don't have token, so we can't fetch emails
            # They will need to be fetched by email service if needed
            
            redis_queue.enqueue_task_event(
                event_type="task_deleted",
                task_id=task.id,
                task_title=task.title,
                assigned_to_id=task.assigned_to,
                reporting_to_id=task.reporting_to,
                assigned_to_email=assigned_to_email,
                reporting_to_email=reporting_to_email,
                updated_by_id=user_id,
                updated_by_email=updated_by_email,
                updated_by_role=user_role,
                organization_id=organization_id,
                organization_name=organization_name
            )
        except Exception as e:
            print(f"[ERROR] Failed to enqueue task deleted event: {str(e)}")
        
        self.repository.delete(task)

    def get_task_logs(self, organization_id: int) -> List[TaskLog]:
        """Get task logs for organization."""
        return self.repository.get_logs_by_organization(organization_id)

