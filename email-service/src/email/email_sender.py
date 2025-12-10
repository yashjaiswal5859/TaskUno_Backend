"""
Email sending service.
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import logging
from common.config.settings import settings

logger = logging.getLogger(__name__)


def format_changes(changes: Dict[str, Any]) -> str:
    """Format changes dictionary for email."""
    if not changes:
        return "No specific changes listed"
    
    formatted = []
    for key, value in changes.items():
        formatted.append(f"  • {key}: {value}")
    return "\n".join(formatted)


def send_task_notification_email(
    to_email: str,
    event_type: str,  # "task_created", "task_updated", "task_deleted"
    task_id: int,
    task_title: str,
    updated_by_email: Optional[str] = None,
    updated_by_role: Optional[str] = None,
    organization_name: Optional[str] = None,
    changes: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    recipient_type: str = "assigned_to"  # "assigned_to" or "reporting_to"
):
    """Send task notification email with HTML design."""
    try:
        # Create email
        msg = MIMEMultipart('alternative')
        # Use sender_email property (SMTP_FROM_EMAIL or SMTP_USER)
        # If SMTP_FROM_EMAIL is a display name (not an email), format it properly
        sender_email = settings.SMTP_USER or "noreply@scrummaster.com"
        from_email = settings.SMTP_FROM_EMAIL
        
        if from_email and '@' in from_email:
            # SMTP_FROM_EMAIL is an email address
            msg['From'] = from_email
        elif from_email:
            # SMTP_FROM_EMAIL is a display name, use format: "Display Name <email@example.com>"
            msg['From'] = f"{from_email} <{sender_email}>"
        else:
            # No SMTP_FROM_EMAIL, just use sender email
            msg['From'] = sender_email
        
        msg['To'] = to_email
        
        # Determine subject and body based on event type
        if event_type == "task_created":
            subject = f"New Task Assigned: {task_title}"
            action_text = "created"
        elif event_type == "task_updated":
            subject = f"Task Updated: {task_title}"
            action_text = "updated"
        elif event_type == "task_deleted":
            subject = f"Task Deleted: {task_title}"
            action_text = "deleted"
        else:
            subject = f"Task Notification: {task_title}"
            action_text = "modified"
        
        msg['Subject'] = subject
        
        # Format status changes
        status_change = ""
        if changes and 'status' in changes:
            status_value = changes.get('status')
            if isinstance(status_value, dict):
                old_status = status_value.get('old', '')
                new_status = status_value.get('new', '')
                if old_status and new_status:
                    status_change = f"{old_status} → {new_status}"
                elif new_status:
                    status_change = f"Status changed to: {new_status}"
            elif status_value:
                # If status is just a value (not old/new dict), show it
                status_change = f"Status: {status_value}"
        
        # Format other changes
        other_changes = []
        for key, value in (changes or {}).items():
            if key != 'status':
                if isinstance(value, dict):
                    old_val = value.get('old', '')
                    new_val = value.get('new', '')
                    if old_val and new_val:
                        other_changes.append(f"{key}: {old_val} → {new_val}")
                    elif new_val:
                        other_changes.append(f"{key}: {new_val}")
                else:
                    other_changes.append(f"{key}: {value}")
        
        # Updated by email (fallback to "System" if email not available)
        updated_by_display = updated_by_email or "System"
        
        # Action text with role
        action_role = updated_by_role or "User"
        action_title = f"Action: {action_text.title()} by {action_role}"
        action_email_display = updated_by_email if updated_by_email else ""
        
        # Organization name
        org_display = organization_name or "Your Organization"
        
        # HTML email template
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background-color: #ffffff;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .content {{
            padding: 30px 20px;
        }}
        .task-info {{
            background-color: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .task-info h2 {{
            margin: 0 0 15px 0;
            color: #667eea;
            font-size: 20px;
        }}
        .info-row {{
            margin: 10px 0;
            display: flex;
            align-items: center;
        }}
        .info-label {{
            font-weight: 600;
            color: #666;
            min-width: 120px;
        }}
        .info-value {{
            color: #333;
        }}
        .status-change {{
            background-color: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 6px;
            padding: 15px;
            margin: 20px 0;
            text-align: center;
        }}
        .status-change strong {{
            color: #1976d2;
            font-size: 18px;
        }}
        .changes-list {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .changes-list ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .changes-list li {{
            margin: 5px 0;
        }}
        .reason-box {{
            background-color: #f0f0f0;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
            border-left: 4px solid #9e9e9e;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            border-top: 1px solid #e0e0e0;
        }}
        .signature {{
            margin-top: 20px;
            text-align: center;
        }}
        .action-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .action-box strong {{
            font-size: 18px;
            display: block;
            margin-bottom: 8px;
        }}
        .action-box .action-email {{
            font-size: 14px;
            opacity: 0.9;
            margin-top: 5px;
        }}
        .logo-container {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin-bottom: 15px;
        }}
        .logo-icon {{
            font-size: 32px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .logo-text {{
            font-size: 28px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: 1px;
        }}
        .btn {{
            display: inline-block;
            padding: 12px 24px;
            background-color: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin-top: 20px;
            transition: background-color 0.3s;
        }}
        .btn:hover {{
            background-color: #5568d3;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{org_display}</h1>
        </div>
        
        <div class="content">
            <p>Hello,</p>
            <p>A task has been <strong>{action_text}</strong> and you are involved in this task.</p>
            
            <div class="action-box">
                <strong>{action_title}</strong>
                {f'<div class="action-email">{action_email_display}</div>' if action_email_display else ''}
            </div>
            
            <div class="task-info">
                <h2>Task Details</h2>
                <div class="info-row">
                    <span class="info-label">Task ID:</span>
                    <span class="info-value">#{task_id}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Task Title:</span>
                    <span class="info-value"><strong>{task_title}</strong></span>
                </div>
            </div>
            
            {f'<div class="status-change"><strong>Status Changes:</strong><br>{status_change}</div>' if status_change else ''}
            
            {f'<div class="changes-list"><strong>Other Changes:</strong><ul>' + ''.join([f'<li>{change}</li>' for change in other_changes]) + '</ul></div>' if other_changes else ''}
            
            {f'<div class="reason-box"><strong>Reason:</strong><br>{reason}</div>' if reason else ''}
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="http://localhost:3000/task/{task_id}" class="btn">View Task</a>
            </div>
        </div>
        
        <div class="footer">
            <div class="signature">
                <div class="logo-container">
                    <span class="logo-icon">📋</span>
                    <span class="logo-text">TaskUno</span>
                </div>
                <p style="color: #666; margin: 5px 0; font-weight: 500;">Task Management System</p>
                <p style="color: #999; font-size: 12px; margin-top: 10px;">
                    This is an automated notification. Please do not reply to this email.
                </p>
            </div>
        </div>
    </div>
</body>
</html>
"""
        
        # Plain text version (fallback)
        text_body = f"""
Hello,

A task has been {action_text} and you are involved in this task.

{action_title}{f' ({action_email_display})' if action_email_display else ''}

Task Details:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Task ID: {task_id}
Task Title: {task_title}
"""
        
        if status_change:
            text_body += f"\nStatus Changes: {status_change}\n"
        
        if other_changes:
            text_body += f"\nOther Changes:\n"
            for change in other_changes:
                text_body += f"  • {change}\n"
        
        if reason:
            text_body += f"\nReason: {reason}\n"
        
        text_body += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

View task: http://localhost:3000/task/{task_id}

Best regards,
TaskUno
Task Management System
"""
        
        # Attach both HTML and plain text
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email if SMTP is configured
        if not settings.SMTP_HOST:
            logger.warning(f"⚠️  SMTP_HOST not configured in .env file")
            logger.info(f"Would send email to {to_email} for task {task_id} ({event_type})")
            logger.info(f"Email content:\n{body}")
            return True  # Return True so event is marked as processed
        
        if not settings.SMTP_USER:
            logger.warning(f"⚠️  SMTP_USER (sender email) not configured in .env file")
            logger.info(f"Would send email to {to_email} for task {task_id} ({event_type})")
            logger.info(f"Email content:\n{body}")
            return True
        
        if not settings.SMTP_PASSWORD:
            logger.warning(f"⚠️  SMTP_PASSWORD (sender password) not configured in .env file")
            logger.info(f"Would send email to {to_email} for task {task_id} ({event_type})")
            logger.info(f"Email content:\n{body}")
            return True
        
        # All SMTP settings are configured, send email
        try:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            if settings.SMTP_USE_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            logger.info(f"✅ Email sent to {to_email} for task {task_id} ({event_type})")
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ SMTP Authentication failed. Check SMTP_USER and SMTP_PASSWORD in .env file: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to send email to {to_email}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        
    except Exception as e:
        logger.error(f"❌ Error sending email to {to_email}: {str(e)}")
        return False

