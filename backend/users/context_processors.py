from .models import Notification
from chat.models import Message

def notifications_processor(request):
    if request.user.is_authenticated:
        unread_notifications = request.user.notifications.filter(is_read=False)[:5]
        unread_count = request.user.notifications.filter(is_read=False).count()
        
        # Count unread messages where user is NOT the sender
        unread_messages_count = Message.objects.filter(
            thread__first_user=request.user,
            is_read=False
        ).exclude(sender=request.user).count() + Message.objects.filter(
            thread__second_user=request.user,
            is_read=False
        ).exclude(sender=request.user).count()

        return {
            'unread_notifications': unread_notifications,
            'unread_count': unread_count,
            'unread_messages_count': unread_messages_count
        }
    return {}
