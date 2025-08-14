# core/context_processors.py

from .models import Notification, Follow

def notifications_and_following(request):
    context = {}
    if request.user.is_authenticated:
        
        unread_notifications_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        following_count = Follow.objects.filter(follower=request.user).count()

        context = {
            'unread_notifications_count': unread_notifications_count,
            'following_count': following_count,
        }
    return context