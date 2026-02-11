"""
Kibray Email Service
====================
Centralized email sending with professional HTML templates.

Usage:
    from core.services.email_service import KibrayEmailService
    
    # Send welcome email with credentials
    KibrayEmailService.send_welcome_credentials(
        to_email="client@example.com",
        first_name="John",
        email="client@example.com",
        temp_password="Xy7k9mN2",
        login_url="https://app.kibray.com/login/",
        project_name="Smith Residence",  # optional
        sender_name="Jesus Duran"
    )
"""

import contextlib
import logging
from typing import Optional

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class KibrayEmailService:
    """
    Professional email service with HTML templates for Kibray Painting.
    All emails are sent with both HTML and plain text versions.
    """
    
    @classmethod
    def _get_default_from_email(cls):
        """Get the default from email from settings, with fallback."""
        return getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@kibraypainting.us')
    
    @classmethod
    def _send_email(
        cls,
        subject: str,
        template_name: str,
        context: dict,
        to_emails: list,
        from_email: Optional[str] = None,
        fail_silently: bool = True
    ) -> bool:
        """
        Internal method to send email with HTML template.
        
        Args:
            subject: Email subject line
            template_name: Path to the HTML template (e.g., 'emails/welcome_credentials.html')
            context: Dictionary of context variables for the template
            to_emails: List of recipient email addresses
            from_email: Sender email (defaults to DEFAULT_FROM_EMAIL)
            fail_silently: If True, suppress exceptions
            
        Returns:
            bool: True if email was sent successfully
        """
        try:
            # Render HTML content
            html_content = render_to_string(template_name, context)
            
            # Create plain text version
            text_content = strip_tags(html_content)
            # Clean up the plain text
            text_content = '\n'.join(line.strip() for line in text_content.split('\n') if line.strip())
            
            # Create email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email or cls._get_default_from_email(),
                to=to_emails
            )
            email.attach_alternative(html_content, "text/html")
            
            # Send
            email.send(fail_silently=fail_silently)
            
            logger.info(f"Email sent successfully to {to_emails}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_emails}: {e}")
            if not fail_silently:
                raise
            return False
    
    @classmethod
    def send_welcome_credentials(
        cls,
        to_email: str,
        first_name: str,
        email: str,
        temp_password: str,
        login_url: str,
        sender_name: str = "Kibray Painting",
        project_name: Optional[str] = None,
        fail_silently: bool = True
    ) -> bool:
        """
        Send welcome email with login credentials.
        
        Used when:
        - Creating a new client
        - Adding an owner/client to a project
        - Creating a user via API
        """
        context = {
            'first_name': first_name,
            'email': email,
            'temp_password': temp_password,
            'login_url': login_url,
            'sender_name': sender_name,
            'project_name': project_name,
        }
        
        subject = f"Welcome to Kibray Painting"
        if project_name:
            subject = f"Project Access: {project_name}"
        
        return cls._send_email(
            subject=subject,
            template_name='emails/welcome_credentials.html',
            context=context,
            to_emails=[to_email],
            fail_silently=fail_silently
        )
    
    @classmethod
    def send_password_reset(
        cls,
        to_email: str,
        email: str,
        new_password: str,
        login_url: str,
        fail_silently: bool = True
    ) -> bool:
        """
        Send password reset notification.
        
        Used when admin resets a user's password.
        """
        context = {
            'email': email,
            'new_password': new_password,
            'login_url': login_url,
        }
        
        return cls._send_email(
            subject="Password Reset - Kibray Painting",
            template_name='emails/password_reset.html',
            context=context,
            to_emails=[to_email],
            fail_silently=fail_silently
        )
    
    @classmethod
    def send_changeorder_signed_notification(
        cls,
        to_emails: list,
        co_number: int,
        project_name: str,
        description: str,
        pricing_type: str,
        signed_by: str,
        signed_at: str,
        amount: Optional[str] = None,
        rate_info: Optional[str] = None,
        view_url: Optional[str] = None,
        fail_silently: bool = True
    ) -> bool:
        """
        Notify staff that a change order has been signed.
        
        Used when client signs a CO via the public signing page.
        """
        context = {
            'co_number': co_number,
            'project_name': project_name,
            'description': description[:180] + ('...' if len(description) > 180 else ''),
            'pricing_type': pricing_type,
            'signed_by': signed_by,
            'signed_at': signed_at,
            'amount': amount,
            'rate_info': rate_info,
            'view_url': view_url,
        }
        
        return cls._send_email(
            subject=f"CO #{co_number} Signed by Client",
            template_name='emails/changeorder_signed.html',
            context=context,
            to_emails=to_emails,
            fail_silently=fail_silently
        )
    
    @classmethod
    def send_signature_confirmation(
        cls,
        to_email: str,
        document_type: str,
        document_number: str,
        signed_by: str,
        signed_at: str,
        project_name: Optional[str] = None,
        fail_silently: bool = True
    ) -> bool:
        """
        Send confirmation to client after signing a document.
        
        Used when client signs a CO or color sample.
        """
        context = {
            'document_type': document_type,
            'document_number': document_number,
            'signed_by': signed_by,
            'signed_at': signed_at,
            'project_name': project_name,
        }
        
        return cls._send_email(
            subject=f"Signature Confirmation - {document_type} #{document_number}",
            template_name='emails/signature_confirmation.html',
            context=context,
            to_emails=[to_email],
            fail_silently=fail_silently
        )
    
    @classmethod
    def send_colorsample_signed_notification(
        cls,
        to_email: str,
        color_name: str,
        color_code: str,
        project_name: str,
        signed_by: str,
        signed_at: str,
        client_ip: str,
        location: Optional[str] = None,
        view_url: Optional[str] = None,
        fail_silently: bool = True
    ) -> bool:
        """
        Notify PM that a color sample has been signed.
        
        Used when client signs a color sample via the public signing page.
        """
        context = {
            'color_name': color_name,
            'color_code': color_code,
            'project_name': project_name,
            'signed_by': signed_by,
            'signed_at': signed_at,
            'client_ip': client_ip,
            'location': location,
            'view_url': view_url,
        }
        
        return cls._send_email(
            subject=f"Color Sample Signed: {color_name}",
            template_name='emails/colorsample_signed.html',
            context=context,
            to_emails=[to_email],
            fail_silently=fail_silently
        )
    
    @classmethod
    def send_simple_notification(
        cls,
        to_emails: list,
        subject: str,
        message: str,
        greeting: Optional[str] = None,
        button_url: Optional[str] = None,
        button_text: Optional[str] = None,
        details: Optional[dict] = None,
        closing: Optional[str] = None,
        fail_silently: bool = True
    ) -> bool:
        """
        Send a notification email with Kibray branding.
        
        Args:
            to_emails: List of recipient emails
            subject: Email subject
            message: Main message body
            greeting: Optional greeting (e.g., "Hello John!")
            button_url: Optional CTA button URL
            button_text: Optional CTA button text
            details: Optional dict of key-value pairs to show in info box
            closing: Optional closing message
            fail_silently: If True, suppress exceptions
        
        Returns:
            bool: True if email was sent successfully
        """
        context = {
            'subject': subject,
            'message': message,
            'greeting': greeting,
            'button_url': button_url,
            'button_text': button_text,
            'details': details,
            'closing': closing,
        }
        
        return cls._send_email(
            subject=subject,
            template_name='emails/simple_notification.html',
            context=context,
            to_emails=to_emails,
            fail_silently=fail_silently
        )

    @classmethod
    def send_html_email(
        cls,
        to_email: str,
        subject: str,
        text_content: str,
        html_content: str,
        fail_silently: bool = True
    ) -> bool:
        """
        Send an email with custom HTML content (not using templates).
        
        Used for proposal/estimate emails where content is user-generated.
        """
        try:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=cls._get_default_from_email(),
                to=[to_email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=fail_silently)
            
            logger.info(f"HTML email sent to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send HTML email to {to_email}: {e}")
            if not fail_silently:
                raise
            return False
