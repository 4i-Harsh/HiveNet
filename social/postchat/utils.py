from django.core.mail import send_mail
from django.conf import settings
import logging

# Create a logger for this file
logger = logging.getLogger(__name__)

def send_friend_request_email(from_user, to_user):
    """
    Send an email notification for friend request
    
    Args:
        from_user: User sending the friend request
        to_user: User receiving the friend request
    """
    if not to_user.profile.email:
        logger.warning(f"No email found for user: {to_user.username}")
        return False
        
    try:
        logger.info(f"Attempting to send friend request email from {from_user.username} to {to_user.username}")
        logger.info(f"Sending to email: {to_user.profile.email}")
        
        send_mail(
            subject='New Friend Request on HiveNet',
            message=f'{from_user.username} has sent you a friend request on HiveNet!',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[to_user.profile.email],
            fail_silently=True
        )
        
        logger.info(f"Successfully sent friend request email to {to_user.username}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send friend request email: {str(e)}")
        logger.error(f"From: {from_user.username}, To: {to_user.username}")
        logger.error(f"Email settings: HOST_USER={settings.EMAIL_HOST_USER}")
        return False 