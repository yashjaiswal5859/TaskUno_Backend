"""
Service layer for task business logic.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.tasks.models import Task, TaskLog
from src.tasks.repository.task_repository import TaskRepository
from src.tasks.schemas import TaskBase, TaskUpdate
from src.auth.models import Developer, ProductOwner
from src.project.models import Project


class TaskService:
    """Service for task operations."""

    def __init__(self, db: Session):
        self.repository = TaskRepository(db)
        self.db = db

    def create_task(self, task_data: TaskBase, created_by_id: int, organization_id: int) -> Task:
        """Create a new task. Only Product Owner can create tasks."""
        # Verify project belongs to organization
        project = self.repository.db.query(Project).filter(Project.id == task_data.project_id).first()
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
        
        # If assigned_to is provided, verify developer belongs to organization
        if task_data.assigned_to:
            developer = self.repository.db.query(Developer).filter(Developer.id == task_data.assigned_to).first()
            if not developer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Developer not found"
                )
            # Check if developer belongs to the organization
            if developer.organization_id != organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Developer does not belong to your organization"
                )
        
        # Use reporting_to if provided, otherwise use created_by_id (current user)
        reporting_to_id = task_data.reporting_to if task_data.reporting_to else created_by_id
        
        # Verify reporting_to (Product Owner) belongs to organization
        if reporting_to_id:
            reporting_to_po = self.repository.db.query(ProductOwner).filter(ProductOwner.id == reporting_to_id).first()
            if not reporting_to_po:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Reporting to Product Owner not found"
                )
            if reporting_to_po.organization_id != organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Reporting to Product Owner does not belong to your organization"
                )
        
        task_dict = {
            "title": task_data.title,
            "description": task_data.description,
            "status": task_data.status,
            "project_id": task_data.project_id,
            "owner_id": created_by_id,  # Keep for backward compatibility
            "createdDate": datetime.now(),
            "dueDate": task_data.dueDate,
            "assigned_to": task_data.assigned_to,
            "created_by_id": reporting_to_id,  # Use reporting_to as created_by_id
            "created_by_type": "product_owner"
        }
        new_task = self.repository.create(task_dict)
        
        # Send email notification to reporting_to and assigned_to when task is created
        self._send_task_creation_email(new_task, created_by_id, organization_id)
        
        return new_task

    def get_task_by_id(self, task_id: int, owner_id: int) -> Task:
        """Get task by ID."""
        # Use get_by_id_with_org_check if we need org check, otherwise use regular get_by_id
        # For now, use regular get_by_id - org check is done in controller
        task = self.repository.get_by_id(task_id, owner_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task Not Found!"
            )
        return task

    def get_all_tasks(self, organization_id: int) -> List[Task]:
        """Get all tasks for organization."""
        return self.repository.get_all_by_organization_id(organization_id)

    def get_all_tasks_admin(self) -> List[Task]:
        """Get all tasks (admin only)."""
        return self.repository.get_all()

    def update_task(self, task_id: int, task_data: TaskUpdate, user_role: str, user_id: int, organization_id: int) -> Task:
        """Update a task. Only assigned Developer can update status. Product Owners can update all fields."""
        print(f"\n{'='*60}")
        print(f"[TASK UPDATE] ========== TASK UPDATE STARTED ==========")
        print(f"[TASK UPDATE] Task ID: {task_id}")
        print(f"[TASK UPDATE] User ID: {user_id}")
        print(f"[TASK UPDATE] User Role: {user_role}")
        print(f"[TASK UPDATE] Organization ID: {organization_id}")
        print(f"[TASK UPDATE] Update Data: {task_data.model_dump(exclude_unset=True)}")
        print(f"{'='*60}\n")
        
        task = self.repository.get_by_id_with_org_check(task_id, organization_id)
        if not task:
            print(f"[TASK UPDATE] ✗ Task not found!")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task Not Found!"
            )
        
        print(f"[TASK UPDATE] ✓ Task found:")
        print(f"[TASK UPDATE]   Task ID: {task.id}")
        print(f"[TASK UPDATE]   Task Title: {task.title}")
        print(f"[TASK UPDATE]   Current Status: {task.status}")
        print(f"[TASK UPDATE]   Assigned To: {task.assigned_to}")
        print(f"[TASK UPDATE]   Created By ID: {task.created_by_id}")
        
        # If Developer, check if they are assigned to this task
        if user_role == "Developer":
            print(f"\n[TASK UPDATE] User is Developer - checking assignment...")
            print(f"[TASK UPDATE]   Task assigned_to: {task.assigned_to}")
            print(f"[TASK UPDATE]   Current user_id: {user_id}")
            
            # Check if developer is assigned to this task
            if not task.assigned_to or task.assigned_to != user_id:
                print(f"[TASK UPDATE] ✗ Developer not assigned to this task!")
                print(f"[TASK UPDATE]   Task is assigned to: {task.assigned_to}")
                print(f"[TASK UPDATE]   User ID is: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only the assigned developer can update this task status"
                )
            
            print(f"[TASK UPDATE] ✓ Developer is assigned to this task")
            
            # Only allow status and status_change_reason updates
            update_dict = task_data.model_dump(exclude_unset=True)
            print(f"[TASK UPDATE] Update fields: {list(update_dict.keys())}")
            allowed_fields = {'status', 'status_change_reason'}
            if not all(key in allowed_fields for key in update_dict.keys()):
                print(f"[TASK UPDATE] ✗ Invalid fields for Developer update!")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Developers can only update task status"
                )
            print(f"[TASK UPDATE] ✓ All fields are allowed for Developer")
        
        old_status = task.status
        update_dict = task_data.model_dump(exclude_unset=True)
        
        print(f"\n[TASK UPDATE] Processing status change...")
        print(f"[TASK UPDATE]   Old Status: {old_status}")
        
        # Extract status_change_reason if present
        reason = update_dict.pop('status_change_reason', None)
        new_status = update_dict.get('status', old_status)
        
        print(f"[TASK UPDATE]   New Status: {new_status}")
        print(f"[TASK UPDATE]   Reason: {reason}")
        print(f"[TASK UPDATE]   Status Changed: {old_status != new_status}")
        
        # If Product Owner is updating assigned_to, verify developer belongs to organization
        if 'assigned_to' in update_dict and update_dict['assigned_to']:
            developer = self.repository.db.query(Developer).filter(Developer.id == update_dict['assigned_to']).first()
            if not developer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Developer not found"
                )
            # Check if developer belongs to the organization
            if developer.organization_id != organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Developer does not belong to your organization"
                )
        
        # If Product Owner is updating created_by_id, verify Product Owner belongs to organization
        if 'created_by_id' in update_dict and update_dict['created_by_id']:
            from src.auth.models import ProductOwner
            product_owner = self.repository.db.query(ProductOwner).filter(ProductOwner.id == update_dict['created_by_id']).first()
            if not product_owner:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Product Owner not found"
                )
            # Check if Product Owner belongs to the organization
            if product_owner.organization_id != organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Product Owner does not belong to your organization"
                )
        
        print(f"\n[TASK UPDATE] Updating task in database...")
        updated_task = self.repository.update(task, update_dict)
        print(f"[TASK UPDATE] ✓ Task updated in database")
        print(f"[TASK UPDATE]   Updated Status: {updated_task.status}")
        
        # Create log entry with reason if status changed
        if old_status != new_status:
            print(f"\n[TASK UPDATE] Status changed - creating log entry...")
            self.repository.create_log(
                task_id=task_id,
                reason=reason,
                old_status=old_status,
                new_status=new_status
            )
            print(f"[TASK UPDATE] ✓ Log entry created")
            
            # Send email notification whenever status changes (to all assignees and assigner)
            print(f"\n[TASK UPDATE] ========== CHECKING EMAIL TRIGGER ==========")
            print(f"[TASK UPDATE] Checking if email should be sent...")
            print(f"[TASK UPDATE]   user_role: {user_role}")
            print(f"[TASK UPDATE]   user_id: {user_id}")
            print(f"[TASK UPDATE]   task.created_by_id: {task.created_by_id}")
            print(f"[TASK UPDATE]   old_status: {old_status}")
            print(f"[TASK UPDATE]   new_status: {new_status}")
            print(f"[TASK UPDATE]   reason: {reason}")
            
            # Use updated_task to get the latest created_by_id (in case it was updated)
            created_by_id = updated_task.created_by_id if hasattr(updated_task, 'created_by_id') else task.created_by_id
            
            # Send email whenever status changes, regardless of who changed it
            if created_by_id or updated_task.assigned_to:
                print(f"[TASK UPDATE] ✓ Task has recipients (created_by_id or assigned_to)")
                print(f"[TASK UPDATE] ✓✓✓ ALL CONDITIONS MET - TRIGGERING EMAIL ✓✓✓")
                self._queue_status_change_email(updated_task, old_status, new_status, reason, user_id, user_role)
            else:
                print(f"[TASK UPDATE] ✗ Skipping email - task has no recipients")
                print(f"[TASK UPDATE]   Task ID: {task.id}")
                print(f"[TASK UPDATE]   Task created_by_id: {created_by_id}")
                print(f"[TASK UPDATE]   Task assigned_to: {updated_task.assigned_to}")
        else:
            print(f"\n[TASK UPDATE] Status did not change - no email needed")
            print(f"[TASK UPDATE]   Old: {old_status}, New: {new_status}")
        
        print(f"\n{'='*60}")
        print(f"[TASK UPDATE] ========== TASK UPDATE COMPLETED ==========")
        print(f"{'='*60}\n")
        
        return updated_task
    
    def _send_task_creation_email(self, task: Task, creator_id: int, organization_id: int):
        """Send email notification when task is created to reporting_to and assigned_to."""
        print(f"\n{'='*60}")
        print(f"[TASK CREATION EMAIL] ========== EMAIL NOTIFICATION STARTED ==========")
        print(f"[TASK CREATION EMAIL] Task ID: {task.id}")
        print(f"[TASK CREATION EMAIL] Task Title: {task.title}")
        print(f"{'='*60}\n")
        
        try:
            from src.notifications.service.email_service import EmailService
            import threading
            
            # Collect email recipients
            recipients = []
            
            # Get reporting_to (Product Owner who will receive reports)
            print(f"[TASK CREATION EMAIL STEP 1] Getting reporting_to (Product Owner)...")
            if task.created_by_id:
                reporting_to = self.repository.db.query(ProductOwner).filter(ProductOwner.id == task.created_by_id).first()
                if reporting_to:
                    reporting_to_name = f"{reporting_to.firstName} {reporting_to.lastName}" if reporting_to.firstName and reporting_to.lastName else reporting_to.username
                    recipients.append({
                        "email": reporting_to.email,
                        "name": reporting_to_name,
                        "role": "Reporting To (Product Owner)"
                    })
                    print(f"[TASK CREATION EMAIL STEP 1] ✓ Reporting To found!")
                    print(f"[TASK CREATION EMAIL STEP 1]   Product Owner ID: {reporting_to.id}")
                    print(f"[TASK CREATION EMAIL STEP 1]   Product Owner Email: {reporting_to.email}")
                    print(f"[TASK CREATION EMAIL STEP 1]   Product Owner Name: {reporting_to_name}")
                else:
                    print(f"[TASK CREATION EMAIL STEP 1] ✗ WARNING: Reporting To not found!")
            
            # Get assigned_to (Developer)
            print(f"\n[TASK CREATION EMAIL STEP 2] Getting assigned_to (Developer)...")
            if task.assigned_to:
                assigned_developer = self.repository.db.query(Developer).filter(Developer.id == task.assigned_to).first()
                if assigned_developer:
                    assigned_dev_name = f"{assigned_developer.firstName} {assigned_developer.lastName}" if assigned_developer.firstName and assigned_developer.lastName else assigned_developer.username
                    recipients.append({
                        "email": assigned_developer.email,
                        "name": assigned_dev_name,
                        "role": "Assigned Developer"
                    })
                    print(f"[TASK CREATION EMAIL STEP 2] ✓ Assigned Developer found!")
                    print(f"[TASK CREATION EMAIL STEP 2]   Developer ID: {assigned_developer.id}")
                    print(f"[TASK CREATION EMAIL STEP 2]   Developer Email: {assigned_developer.email}")
                    print(f"[TASK CREATION EMAIL STEP 2]   Developer Name: {assigned_dev_name}")
                else:
                    print(f"[TASK CREATION EMAIL STEP 2] ✗ WARNING: Assigned Developer not found!")
            else:
                print(f"[TASK CREATION EMAIL STEP 2] ℹ Task is not assigned to any developer")
            
            if not recipients:
                print(f"\n[TASK CREATION EMAIL] ✗ No recipients found - skipping email notification")
                return
            
            # Get creator info
            print(f"\n[TASK CREATION EMAIL STEP 3] Getting task creator...")
            creator = self.repository.db.query(ProductOwner).filter(ProductOwner.id == creator_id).first()
            creator_name = "Product Owner"
            if creator:
                creator_name = f"{creator.firstName} {creator.lastName}" if creator.firstName and creator.lastName else creator.username
                print(f"[TASK CREATION EMAIL STEP 3] ✓ Creator found: {creator_name}")
            
            print(f"\n[TASK CREATION EMAIL STEP 4] Creating email content...")
            subject = f"New Task Created: {task.title}"
            body = f"""New Task Created Notification

Task: {task.title}
Description: {task.description or 'No description'}
Project: {task.project.title if task.project else 'N/A'}
Status: {task.status}
Due Date: {task.dueDate.strftime('%Y-%m-%d') if task.dueDate else 'Not set'}
Created By: {creator_name}

This task has been assigned to you. Please review and start working on it.

---
This is an automated notification from TaskUno.
"""
            
            print(f"[TASK CREATION EMAIL STEP 4] ✓ Email content created")
            print(f"[TASK CREATION EMAIL STEP 4]   Subject: {subject}")
            print(f"[TASK CREATION EMAIL STEP 4]   Recipients: {len(recipients)}")
            for i, recipient in enumerate(recipients, 1):
                print(f"[TASK CREATION EMAIL STEP 4]     {i}. {recipient['name']} ({recipient['email']}) - {recipient['role']}")
            
            print(f"\n[TASK CREATION EMAIL STEP 5] Starting background thread for async email sending...")
            email_service = EmailService(self.repository.db)
            
            def send_emails_async():
                """Send emails to all recipients in background thread."""
                print(f"\n[TASK CREATION EMAIL ASYNC] ========== BACKGROUND THREAD STARTED ==========")
                print(f"[TASK CREATION EMAIL ASYNC] Thread ID: {threading.current_thread().ident}")
                
                success_count = 0
                fail_count = 0
                
                for recipient in recipients:
                    try:
                        print(f"\n[TASK CREATION EMAIL ASYNC] Sending email to {recipient['name']} ({recipient['email']})...")
                        success = email_service.send_email_direct(recipient['email'], subject, body)
                        
                        if success:
                            success_count += 1
                            print(f"[TASK CREATION EMAIL ASYNC] ✓✓✓ SUCCESS: Email sent to {recipient['email']} ✓✓✓")
                        else:
                            fail_count += 1
                            print(f"[TASK CREATION EMAIL ASYNC] ✗✗✗ FAILED: Email failed for {recipient['email']} ✗✗✗")
                    except Exception as e:
                        fail_count += 1
                        print(f"[TASK CREATION EMAIL ASYNC] ✗✗✗ EXCEPTION sending to {recipient['email']}! ✗✗✗")
                        print(f"[TASK CREATION EMAIL ASYNC]   Error: {str(e)}")
                        import traceback
                        traceback.print_exc()
                
                print(f"\n[TASK CREATION EMAIL ASYNC] ========== EMAIL SENDING SUMMARY ==========")
                print(f"[TASK CREATION EMAIL ASYNC] Total Recipients: {len(recipients)}")
                print(f"[TASK CREATION EMAIL ASYNC] Successful: {success_count}")
                print(f"[TASK CREATION EMAIL ASYNC] Failed: {fail_count}")
                print(f"[TASK CREATION EMAIL ASYNC] ========== BACKGROUND THREAD COMPLETED ==========\n")
            
            thread = threading.Thread(target=send_emails_async, daemon=True, name="TaskCreationEmailSender")
            thread.start()
            print(f"[TASK CREATION EMAIL STEP 5] ✓ Thread started successfully")
            
            print(f"\n{'='*60}")
            print(f"[TASK CREATION EMAIL] ========== EMAIL NOTIFICATION QUEUED ==========")
            print(f"{'='*60}\n")
            
        except Exception as e:
            print(f"\n[TASK CREATION EMAIL] ✗✗✗ EXCEPTION in _send_task_creation_email! ✗✗✗")
            print(f"[TASK CREATION EMAIL]   Error: {str(e)}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")
    
    def _queue_status_change_email(self, task: Task, old_status: str, new_status: str, reason: str, changer_id: int, changer_role: str):
        """Send email notification instantly for task status change to all assignees and assigner."""
        print(f"\n{'='*60}")
        print(f"[EMAIL] ========== EMAIL NOTIFICATION STARTED ==========")
        print(f"[EMAIL] Task ID: {task.id}")
        print(f"[EMAIL] Task Title: {task.title}")
        print(f"{'='*60}\n")
        
        try:
            from src.notifications.service.email_service import EmailService
            import threading
            
            # Collect email recipients - only assigned_to and reporting_to (created_by_id)
            recipients = []
            
            print(f"[EMAIL STEP 1] Getting reporting_to (Product Owner who receives reports)...")
            print(f"[EMAIL STEP 1]   Looking for ProductOwner with ID: {task.created_by_id}")
            
            # Get reporting_to (Product Owner who created the task / receives reports)
            reporting_to = self.repository.db.query(ProductOwner).filter(ProductOwner.id == task.created_by_id).first()
            if reporting_to:
                reporting_to_name = f"{reporting_to.firstName} {reporting_to.lastName}" if reporting_to.firstName and reporting_to.lastName else reporting_to.username
                recipients.append({
                    "email": reporting_to.email,
                    "name": reporting_to_name,
                    "role": "Reporting To (Product Owner)"
                })
                print(f"[EMAIL STEP 1] ✓ Reporting To found!")
                print(f"[EMAIL STEP 1]   Product Owner ID: {reporting_to.id}")
                print(f"[EMAIL STEP 1]   Product Owner Email: {reporting_to.email}")
                print(f"[EMAIL STEP 1]   Product Owner Name: {reporting_to_name}")
            else:
                print(f"[EMAIL STEP 1] ✗ WARNING: Reporting To not found!")
                print(f"[EMAIL STEP 1]   Task created_by_id: {task.created_by_id}")
            
            print(f"\n[EMAIL STEP 2] Getting assigned developer...")
            if task.assigned_to:
                print(f"[EMAIL STEP 2]   Looking for Developer with ID: {task.assigned_to}")
                assigned_developer = self.repository.db.query(Developer).filter(Developer.id == task.assigned_to).first()
                if assigned_developer:
                    assigned_dev_name = f"{assigned_developer.firstName} {assigned_developer.lastName}" if assigned_developer.firstName and assigned_developer.lastName else assigned_developer.username
                    recipients.append({
                        "email": assigned_developer.email,
                        "name": assigned_dev_name,
                        "role": "Assigned Developer"
                    })
                    print(f"[EMAIL STEP 2] ✓ Assigned Developer found!")
                    print(f"[EMAIL STEP 2]   Developer ID: {assigned_developer.id}")
                    print(f"[EMAIL STEP 2]   Developer Email: {assigned_developer.email}")
                    print(f"[EMAIL STEP 2]   Developer Name: {assigned_dev_name}")
                else:
                    print(f"[EMAIL STEP 2] ✗ WARNING: Assigned Developer not found for ID: {task.assigned_to}")
            else:
                print(f"[EMAIL STEP 2] ℹ Task is not assigned to any developer")
            
            if not recipients:
                print(f"\n[EMAIL] ✗ No recipients found - skipping email notification")
                return
            
            print(f"\n[EMAIL STEP 3] Getting user who changed status...")
            print(f"[EMAIL STEP 3]   Looking for {changer_role} with ID: {changer_id}")
            
            # Get user who changed the status (could be Developer or Product Owner)
            changer_name = "User"
            changer_email = "N/A"
            if changer_role == "Developer":
                status_changer = self.repository.db.query(Developer).filter(Developer.id == changer_id).first()
                if status_changer:
                    if status_changer.firstName and status_changer.lastName:
                        changer_name = f"{status_changer.firstName} {status_changer.lastName}"
                    else:
                        changer_name = status_changer.username
                    changer_email = status_changer.email
                    print(f"[EMAIL STEP 3] ✓ Status Changer (Developer) found!")
                    print(f"[EMAIL STEP 3]   Developer ID: {status_changer.id}")
                    print(f"[EMAIL STEP 3]   Developer Name: {changer_name}")
                    print(f"[EMAIL STEP 3]   Developer Email: {changer_email}")
                else:
                    print(f"[EMAIL STEP 3] ✗ WARNING: Status Changer (Developer) not found for ID: {changer_id}")
                    print(f"[EMAIL STEP 3]   Using default values")
            elif changer_role == "Product Owner" or changer_role == "admin":
                status_changer = self.repository.db.query(ProductOwner).filter(ProductOwner.id == changer_id).first()
                if status_changer:
                    if status_changer.firstName and status_changer.lastName:
                        changer_name = f"{status_changer.firstName} {status_changer.lastName}"
                    else:
                        changer_name = status_changer.username
                    changer_email = status_changer.email
                    print(f"[EMAIL STEP 3] ✓ Status Changer (Product Owner) found!")
                    print(f"[EMAIL STEP 3]   Product Owner ID: {status_changer.id}")
                    print(f"[EMAIL STEP 3]   Product Owner Name: {changer_name}")
                    print(f"[EMAIL STEP 3]   Product Owner Email: {changer_email}")
                else:
                    print(f"[EMAIL STEP 3] ✗ WARNING: Status Changer (Product Owner) not found for ID: {changer_id}")
                    print(f"[EMAIL STEP 3]   Using default values")
            else:
                print(f"[EMAIL STEP 3] ✗ WARNING: Unknown role: {changer_role}")
                print(f"[EMAIL STEP 3]   Using default values")
            
            print(f"\n[EMAIL STEP 4] Creating email content...")
            # Create email with prev status, current status, reason, and who changed it
            subject = f"Task Status Updated: {task.title}"
            body = f"""Task Status Update Notification

Task: {task.title}
Project: {task.project.title if task.project else 'N/A'}
Previous Status: {old_status}
Current Status: {new_status}
Status Changed By: {changer_name} ({changer_email}) - {changer_role}
Reason: {reason or 'No reason provided'}

Please review the task status change.

---
This is an automated notification from the Scrum Management System.
"""
            
            print(f"[EMAIL STEP 4] ✓ Email content created")
            print(f"[EMAIL STEP 4]   Subject: {subject}")
            print(f"[EMAIL STEP 4]   Body length: {len(body)} characters")
            print(f"[EMAIL STEP 4]   Recipients: {len(recipients)}")
            for i, recipient in enumerate(recipients, 1):
                print(f"[EMAIL STEP 4]     {i}. {recipient['name']} ({recipient['email']}) - {recipient['role']}")
            
            print(f"\n[EMAIL STEP 5] Starting background thread for async email sending...")
            email_service = EmailService(self.repository.db)
            
            def send_emails_async():
                """Send emails to all recipients in background thread."""
                print(f"\n[EMAIL ASYNC] ========== BACKGROUND THREAD STARTED ==========")
                print(f"[EMAIL ASYNC] Thread ID: {threading.current_thread().ident}")
                print(f"[EMAIL ASYNC] Thread Name: {threading.current_thread().name}")
                
                success_count = 0
                fail_count = 0
                
                for recipient in recipients:
                    try:
                        print(f"\n[EMAIL ASYNC] Sending email to {recipient['name']} ({recipient['email']})...")
                        print(f"[EMAIL ASYNC]   Role: {recipient['role']}")
                        print(f"[EMAIL ASYNC]   Subject: {subject}")
                        
                        success = email_service.send_email_direct(recipient['email'], subject, body)
                        
                        if success:
                            success_count += 1
                            print(f"[EMAIL ASYNC] ✓✓✓ SUCCESS: Email sent to {recipient['email']} ✓✓✓")
                        else:
                            fail_count += 1
                            print(f"[EMAIL ASYNC] ✗✗✗ FAILED: Email failed for {recipient['email']} ✗✗✗")
                            print(f"[EMAIL ASYNC]   Check logs above for error details")
                    except Exception as e:
                        fail_count += 1
                        print(f"[EMAIL ASYNC] ✗✗✗ EXCEPTION sending to {recipient['email']}! ✗✗✗")
                        print(f"[EMAIL ASYNC]   Error: {str(e)}")
                        import traceback
                        traceback.print_exc()
                
                print(f"\n[EMAIL ASYNC] ========== EMAIL SENDING SUMMARY ==========")
                print(f"[EMAIL ASYNC] Total Recipients: {len(recipients)}")
                print(f"[EMAIL ASYNC] Successful: {success_count}")
                print(f"[EMAIL ASYNC] Failed: {fail_count}")
                print(f"[EMAIL ASYNC] ========== BACKGROUND THREAD COMPLETED ==========\n")
            
            # Start background thread
            print(f"[EMAIL STEP 5] Creating background thread...")
            thread = threading.Thread(target=send_emails_async, daemon=True, name="EmailSender")
            print(f"[EMAIL STEP 5] Starting thread...")
            thread.start()
            print(f"[EMAIL STEP 5] ✓ Thread started successfully")
            print(f"[EMAIL STEP 5]   Thread ID: {thread.ident}")
            print(f"[EMAIL STEP 5]   Thread Name: {thread.name}")
            print(f"[EMAIL STEP 5]   Thread is_alive: {thread.is_alive()}")
            print(f"[EMAIL STEP 5] API will respond now (non-blocking)")
            
            print(f"\n{'='*60}")
            print(f"[EMAIL] ========== EMAIL NOTIFICATION QUEUED ==========")
            print(f"{'='*60}\n")
            
        except Exception as e:
            # Log error but don't fail the task update
            print(f"\n[EMAIL] ✗✗✗ EXCEPTION in _queue_status_change_email! ✗✗✗")
            print(f"[EMAIL]   Error: {str(e)}")
            import traceback
            traceback.print_exc()
            print(f"{'='*60}\n")

    def delete_task(self, task_id: int, owner_id: int) -> None:
        """Delete a task."""
        task = self.repository.get_by_id(task_id, owner_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task Not Found!"
            )
        self.repository.delete(task)

    def delete_task_admin(self, task_id: int, db: Session) -> None:
        """Delete a task (admin only)."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task Not Found!"
            )
        self.repository.delete(task)

    def update_task_admin(self, task_id: int, task_data: TaskUpdate, db: Session) -> Task:
        """Update a task (admin only)."""
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task Not Found!"
            )
        update_dict = task_data.model_dump(exclude_unset=True)
        return self.repository.update(task, update_dict)

    def delete_all_tasks(self) -> dict:
        """Delete all tasks (admin only)."""
        self.repository.delete_all()
        return {"message": "All tasks deleted"}

    def get_task_logs(self, owner_id: int) -> List[TaskLog]:
        """Get task logs for owner."""
        return self.repository.get_logs_by_owner(owner_id)

