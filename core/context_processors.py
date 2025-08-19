# In core/context_processors.py

import json
from .models import Notification, Follow

def global_context(request):
    """
    A context processor to add global variables to all templates.
    """
    context = {}
    
    if request.user.is_authenticated:
        # Player state
        last_played_state = None
        if hasattr(request.user, 'userprofile') and request.user.userprofile.last_played_song:
            last_played_song = request.user.userprofile.last_played_song
            last_played_state = {
                'song_src': last_played_song.file_path.url,
                'song_title': last_played_song.title,
                'song_artist': last_played_song.artist,
                'position': request.user.userprofile.playback_position
            }
        
        # Notifications and following counts
        unread_notifications_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        following_count = Follow.objects.filter(follower=request.user).count()

        context = {
            'last_played_state': json.dumps(last_played_state) if last_played_state else '{}',
            'unread_notifications_count': unread_notifications_count,
            'following_count': following_count,
        }
        
    else:
        # Provide default values for unauthenticated users
        context = {
            'last_played_state': '{}',
            'unread_notifications_count': 0,
            'following_count': 0,
        }
        
    return context