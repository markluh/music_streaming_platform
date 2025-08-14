from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone

# The UserProfile model is a OneToOne relationship with Django's built-in User model.
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    last_activity = models.DateTimeField(null=True, blank=True)

    def is_online(self):
        """
        Checks if the user's last activity was within the last 5 minutes.
        """
        if self.last_activity:
            return (timezone.now() - self.last_activity) < timedelta(minutes=5)
        return False

    def __str__(self):
        return f'{self.user.username} Profile'

# The Follow model handles the many-to-many relationship between users.
class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following_set')
    followed = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers_set')
    followed_at = models.DateTimeField(auto_now_add=True)

# The Music model stores information about each uploaded music track.
class Music(models.Model):
    title = models.CharField(max_length=100)
    artist = models.CharField(max_length=100)
    file_path = models.FileField(upload_to='music/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# The LikeDislike model tracks which users like or dislike which music tracks.
class LikeDislike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    music = models.ForeignKey('Music', on_delete=models.CASCADE)
    is_like = models.BooleanField(default=True) # True for a like, False for a dislike
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # This ensures a user can only like or dislike a song once.
        unique_together = ('user', 'music')

    def __str__(self):
        return f"{self.user.username} {'likes' if self.is_like else 'dislikes'} {self.music.title}"

# The Comment model allows users to add comments to a music track.
class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    music = models.ForeignKey('Music', on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.music.title}'



from django.db import models
from .models import User 

class Notification(models.Model):
    
    NEW_FOLLOWER = 'new_follower'
    LIKE = 'like'
    COMMENT = 'comment'
    NEW_MUSIC = 'new_music'


    
    NOTIFICATION_TYPES = (
        (NEW_FOLLOWER, 'New Follower'),
        (LIKE, 'Music Like'),
        (COMMENT, 'Music Comment'),
        (NEW_MUSIC, 'New Music Upload'),
    )

    
    recipient = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    
    
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'{self.sender.username} - {self.get_notification_type_display()}'