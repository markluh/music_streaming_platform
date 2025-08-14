from django.utils import timezone
from .models import UserProfile

class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                user_profile = request.user.userprofile
                user_profile.last_activity = timezone.now()
                user_profile.save(update_fields=['last_activity'])
            except UserProfile.DoesNotExist:
                pass
        
        response = self.get_response(request)
        return response