"""
Service layer for email notifications.
"""
from datetime import datetime
from sqlalchemy.orm import Session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from src.notifications.repository import EmailRepository
from src.notifications.models import EmailQueue
from src.config import settings


class EmailService:
    """Service for email operations."""
    
    def __init__(self, db: Session):
        self.repository = EmailRepository(db)
        self.db = db
    
    def queue_email(self, to_email: str, subject: str, body: str, use_celery: bool = True) -> EmailQueue:
        """
        Queue an email to be sent.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            use_celery: If True, use Celery for async processing. If False, just store in DB.
            
        Returns:
            EmailQueue object
        """
        print(f"[EMAIL QUEUE] Adding email to queue: To={to_email}, Subject={subject}")
        email_data = {
            "to_email": to_email,
            "subject": subject,
            "body": body,
            "status": "pending"
        }
        email_queue_item = self.repository.create(email_data)
        print(f"[EMAIL QUEUE] Email queued successfully with ID: {email_queue_item.id}, Status: {email_queue_item.status}")
        
        # If Celery is enabled, queue the task
        if use_celery:
            try:
                from src.notifications.tasks.email_tasks import send_email_async
                send_email_async.delay(to_email, subject, body)
            except Exception as e:
                # If Celery is not available, just log and continue
                print(f"[EMAIL QUEUE] Warning: Could not queue email via Celery: {str(e)}")
        
        return email_queue_item
    
    def send_email_direct(self, to_email: str, subject: str, body: str) -> bool:
        """
        Send an email directly using SMTP (without queue).
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            
        Returns:
            True if sent successfully, False otherwise
        """
        print(f"\n{'='*60}")
        print(f"[EMAIL SERVICE] ========== SEND EMAIL DIRECT STARTED ==========")
        print(f"{'='*60}\n")
        
        try:
            print(f"[EMAIL SERVICE STEP 1] Email Details:")
            print(f"[EMAIL SERVICE STEP 1]   Recipient: {to_email}")
            print(f"[EMAIL SERVICE STEP 1]   Subject: {subject}")
            print(f"[EMAIL SERVICE STEP 1]   Body length: {len(body)} characters")
            
            print(f"\n[EMAIL SERVICE STEP 2] Checking SMTP configuration from .env file...")
            print(f"[EMAIL SERVICE STEP 2]   SMTP_HOST: {settings.SMTP_HOST}")
            print(f"[EMAIL SERVICE STEP 2]   SMTP_PORT: {settings.SMTP_PORT}")
            print(f"[EMAIL SERVICE STEP 2]   SMTP_USER: {settings.SMTP_USER}")
            print(f"[EMAIL SERVICE STEP 2]   SMTP_USE_TLS: {settings.SMTP_USE_TLS}")
            print(f"[EMAIL SERVICE STEP 2]   SMTP_FROM_EMAIL: {settings.SMTP_FROM_EMAIL}")
            print(f"[EMAIL SERVICE STEP 2]   SMTP_PASSWORD: {'***SET***' if settings.SMTP_PASSWORD else '✗ NOT SET ✗'}")
            
            if not settings.SMTP_HOST or not settings.SMTP_USER:
                print(f"\n[EMAIL SERVICE STEP 2] ✗✗✗ CONFIGURATION ERROR ✗✗✗")
                print(f"[EMAIL SERVICE STEP 2]   SMTP_HOST is {'SET' if settings.SMTP_HOST else 'MISSING'}")
                print(f"[EMAIL SERVICE STEP 2]   SMTP_USER is {'SET' if settings.SMTP_USER else 'MISSING'}")
                print(f"[EMAIL SERVICE STEP 2]   Please check your .env file in backend directory")
                return False
            
            if not settings.SMTP_PASSWORD:
                print(f"\n[EMAIL SERVICE STEP 2] ✗✗✗ CONFIGURATION ERROR ✗✗✗")
                print(f"[EMAIL SERVICE STEP 2]   SMTP_PASSWORD is NOT SET")
                print(f"[EMAIL SERVICE STEP 2]   Please add SMTP_PASSWORD to your .env file")
                return False
            
            print(f"[EMAIL SERVICE STEP 2] ✓ All SMTP settings are configured")
            
            print(f"\n[EMAIL SERVICE STEP 3] Creating email message (MIME)...")
            msg = MIMEMultipart()
            from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            print(f"[EMAIL SERVICE STEP 3]   From: {from_email}")
            print(f"[EMAIL SERVICE STEP 3]   To: {to_email}")
            print(f"[EMAIL SERVICE STEP 3]   Subject: {subject}")
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            print(f"[EMAIL SERVICE STEP 3] ✓ Email message created successfully")
            
            print(f"\n[EMAIL SERVICE STEP 4] Connecting to SMTP server...")
            print(f"[EMAIL SERVICE STEP 4]   Host: {settings.SMTP_HOST}")
            print(f"[EMAIL SERVICE STEP 4]   Port: {settings.SMTP_PORT}")
            
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
                print(f"[EMAIL SERVICE STEP 4] ✓ Connected to SMTP server")
                
                if settings.SMTP_USE_TLS:
                    print(f"\n[EMAIL SERVICE STEP 5] Starting TLS encryption...")
                    server.starttls()
                    print(f"[EMAIL SERVICE STEP 5] ✓ TLS started successfully")
                else:
                    print(f"\n[EMAIL SERVICE STEP 5] TLS disabled (SMTP_USE_TLS=False)")
                
                print(f"\n[EMAIL SERVICE STEP 6] Authenticating with SMTP server...")
                print(f"[EMAIL SERVICE STEP 6]   Username: {settings.SMTP_USER}")
                print(f"[EMAIL SERVICE STEP 6]   Password: {'***' if settings.SMTP_PASSWORD else 'NOT SET'}")
                
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                print(f"[EMAIL SERVICE STEP 6] ✓ Login successful")
                
                print(f"\n[EMAIL SERVICE STEP 7] Sending email message...")
                print(f"[EMAIL SERVICE STEP 7]   From: {from_email}")
                print(f"[EMAIL SERVICE STEP 7]   To: {to_email}")
                
                server.send_message(msg)
                print(f"[EMAIL SERVICE STEP 7] ✓✓✓ Email message sent successfully! ✓✓✓")
            
            print(f"\n{'='*60}")
            print(f"[EMAIL SERVICE] ========== EMAIL SENT SUCCESSFULLY ==========")
            print(f"[EMAIL SERVICE]   Recipient: {to_email}")
            print(f"[EMAIL SERVICE]   Subject: {subject}")
            print(f"{'='*60}\n")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"\n[EMAIL SERVICE] ✗✗✗ SMTP AUTHENTICATION ERROR ✗✗✗")
            print(f"[EMAIL SERVICE]   Error: {str(e)}")
            print(f"[EMAIL SERVICE]   Possible causes:")
            print(f"[EMAIL SERVICE]     - Wrong username or password")
            print(f"[EMAIL SERVICE]     - For Gmail: Need to use App Password, not regular password")
            print(f"[EMAIL SERVICE]     - 2FA not enabled (required for App Passwords)")
            print(f"{'='*60}\n")
            return False
        except smtplib.SMTPConnectError as e:
            print(f"\n[EMAIL SERVICE] ✗✗✗ SMTP CONNECTION ERROR ✗✗✗")
            print(f"[EMAIL SERVICE]   Error: {str(e)}")
            print(f"[EMAIL SERVICE]   Possible causes:")
            print(f"[EMAIL SERVICE]     - Wrong SMTP_HOST or SMTP_PORT")
            print(f"[EMAIL SERVICE]     - Firewall blocking connection")
            print(f"[EMAIL SERVICE]     - SMTP server is down")
            print(f"{'='*60}\n")
            return False
        except smtplib.SMTPException as e:
            print(f"\n[EMAIL SERVICE] ✗✗✗ SMTP ERROR ✗✗✗")
            print(f"[EMAIL SERVICE]   Error: {str(e)}")
            print(f"[EMAIL SERVICE]   Error type: {type(e).__name__}")
            print(f"{'='*60}\n")
            return False
        except Exception as e:
            print(f"\n[EMAIL SERVICE] ✗✗✗ UNEXPECTED EXCEPTION ✗✗✗")
            print(f"[EMAIL SERVICE]   Error: {str(e)}")
            print(f"[EMAIL SERVICE]   Error type: {type(e).__name__}")
            import traceback
            print(f"[EMAIL SERVICE]   Full traceback:")
            traceback.print_exc()
            print(f"{'='*60}\n")
            return False
    
    def send_email(self, email_queue_item: EmailQueue) -> bool:
        """
        Send an email using SMTP.
        
        Args:
            email_queue_item: EmailQueue object to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            print(f"[EMAIL SERVICE] Starting to send email ID: {email_queue_item.id}")
            print(f"[EMAIL SERVICE] Recipient: {email_queue_item.to_email}")
            print(f"[EMAIL SERVICE] Subject: {email_queue_item.subject}")
            
            # Check if SMTP is configured
            print(f"[EMAIL SERVICE] Checking SMTP configuration...")
            print(f"[EMAIL SERVICE]   SMTP_HOST: {settings.SMTP_HOST}")
            print(f"[EMAIL SERVICE]   SMTP_PORT: {settings.SMTP_PORT}")
            print(f"[EMAIL SERVICE]   SMTP_USER: {settings.SMTP_USER}")
            print(f"[EMAIL SERVICE]   SMTP_USE_TLS: {settings.SMTP_USE_TLS}")
            print(f"[EMAIL SERVICE]   SMTP_PASSWORD: {'***' if settings.SMTP_PASSWORD else 'NOT SET'}")
            
            if not settings.SMTP_HOST or not settings.SMTP_USER:
                print("[EMAIL SERVICE] ERROR: SMTP not configured. SMTP_HOST or SMTP_USER is missing.")
                print("[EMAIL SERVICE] Email will be marked as sent but not actually sent.")
                email_queue_item.status = "sent"
                email_queue_item.sent_at = datetime.now()
                self.db.commit()
                return True
            
            if not settings.SMTP_PASSWORD:
                print("[EMAIL SERVICE] ERROR: SMTP_PASSWORD is not set.")
                email_queue_item.status = "failed"
                email_queue_item.retry_count += 1
                self.db.commit()
                return False
            
            # Create message
            print(f"[EMAIL SERVICE] Creating email message...")
            msg = MIMEMultipart()
            from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
            msg['From'] = from_email
            msg['To'] = email_queue_item.to_email
            msg['Subject'] = email_queue_item.subject
            
            print(f"[EMAIL SERVICE] From: {from_email}")
            print(f"[EMAIL SERVICE] To: {email_queue_item.to_email}")
            
            # Add body
            msg.attach(MIMEText(email_queue_item.body, 'plain'))
            print(f"[EMAIL SERVICE] Message created successfully")
            
            # Send email
            print(f"[EMAIL SERVICE] Connecting to SMTP server: {settings.SMTP_HOST}:{settings.SMTP_PORT}")
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                print(f"[EMAIL SERVICE] Connected to SMTP server")
                
                if settings.SMTP_USE_TLS:
                    print(f"[EMAIL SERVICE] Starting TLS...")
                    server.starttls()
                    print(f"[EMAIL SERVICE] TLS started successfully")
                
                print(f"[EMAIL SERVICE] Logging in with user: {settings.SMTP_USER}")
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                print(f"[EMAIL SERVICE] Login successful")
                
                print(f"[EMAIL SERVICE] Sending email message...")
                server.send_message(msg)
                print(f"[EMAIL SERVICE] Email message sent successfully!")
            
            # Mark as sent
            email_queue_item.status = "sent"
            email_queue_item.sent_at = datetime.now()
            self.db.commit()
            print(f"[EMAIL SERVICE] Email marked as sent in database (ID: {email_queue_item.id})")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"[EMAIL SERVICE] ERROR: SMTP Authentication failed: {str(e)}")
            email_queue_item.status = "failed"
            email_queue_item.retry_count += 1
            self.db.commit()
            return False
        except smtplib.SMTPException as e:
            print(f"[EMAIL SERVICE] ERROR: SMTP error occurred: {str(e)}")
            email_queue_item.status = "failed"
            email_queue_item.retry_count += 1
            self.db.commit()
            return False
        except Exception as e:
            # Mark as failed
            print(f"[EMAIL SERVICE] EXCEPTION: Failed to send email {email_queue_item.id}: {str(e)}")
            import traceback
            traceback.print_exc()
            email_queue_item.status = "failed"
            email_queue_item.retry_count += 1
            self.db.commit()
            return False
    
    def process_email_queue(self, limit: int = 10) -> None:
        """
        Process pending emails from the queue.
        
        Args:
            limit: Maximum number of emails to process
        """
        pending_emails = self.repository.get_pending(limit)
        for email in pending_emails:
            self.send_email(email)

