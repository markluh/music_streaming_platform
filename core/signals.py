# core/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Follow, UserProfile
from django.contrib.auth.models import User

@receiver(post_save, sender=Follow)
@receiver(post_delete, sender=Follow)
def update_user_verification_status(sender, instance, **kwargs):
    followed_user = instance.followed
    
    try:
        user_profile = followed_user.userprofile
    except UserProfile.DoesNotExist:
        return

    follower_count = followed_user.followers_set.count()

    if follower_count >= 10 and not user_profile.is_verified:
        user_profile.is_verified = True
        user_profile.save()
    elif follower_count < 10 and user_profile.is_verified:
        user_profile.is_verified = False
        user_profile.save()