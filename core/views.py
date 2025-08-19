from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.db.models import Q
from django.urls import reverse
import json
from django.template.loader import render_to_string
from .forms import CustomUserCreationForm, MusicUploadForm, UserProfileForm
from .models import Music, User, Follow, LikeDislike, Comment, Notification, UserProfile
from django.db.models import Count


# Helper function to check for AJAX
def is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'

#---------------------------------------------------------------------------------------------------------------------------------

def homepage(request):
    music_list = Music.objects.all().order_by('-uploaded_at').prefetch_related(
        'comments__user', 'uploaded_by__userprofile'
    ).annotate(
        likes_count=Count('likedislike', filter=Q(likedislike__is_like=True)),
        dislikes_count=Count('likedislike', filter=Q(likedislike__is_like=False)),
        comments_count=Count('comments', distinct=True)
    )

    followed_users = []
    suggested_users = []
    
    if request.user.is_authenticated:
        following_users_ids = Follow.objects.filter(follower=request.user).values_list('followed_id', flat=True)
        followed_users = User.objects.filter(id__in=following_users_ids)
        
        suggested_users = User.objects.exclude(
            Q(id__in=following_users_ids) | Q(id=request.user.id)
        ).annotate(
            mutual_followers_count=Count(
                'followers_set__follower',
                filter=Q(followers_set__follower__in=followed_users)
            )
        ).order_by('-mutual_followers_count', 'username')[:5]

        for music in music_list:
            music.is_liked = LikeDislike.objects.filter(user=request.user, music=music, is_like=True).exists()
            music.is_disliked = LikeDislike.objects.filter(user=request.user, music=music, is_like=False).exists()

    else:
        for music in music_list:
            music.is_liked = False
            music.is_disliked = False

    context = {
        'all_music': music_list,
        'followed_users': followed_users,
        'suggested_users': suggested_users,
    }
    return render(request, 'core/index.html', context)

#---------------------------------------------------------------------------------------------------------------------------------

@login_required
def upload_music(request):
    if request.method == 'POST':
        form = MusicUploadForm(request.POST, request.FILES)
        if form.is_valid():
            music = form.save(commit=False)
            music.uploaded_by = request.user
            music.save()
            
            followers = Follow.objects.filter(followed=request.user)
            for follow_obj in followers: 
                Notification.objects.create(
                    recipient=follow_obj.follower, 
                    sender=request.user, 
                    notification_type=Notification.NEW_MUSIC, 
                    message=f'{request.user.username} uploaded a new song: {music.title}.'
                )
            
            # For AJAX form submissions, we don't redirect
            if is_ajax(request):
                return render(request, 'core/upload_music.html', {'form': MusicUploadForm(), 'message': 'Music uploaded successfully!'})
            return redirect('homepage')
    else:
        form = MusicUploadForm()
        
    context = {'form': form}
    if is_ajax(request):
        return render(request, 'core/upload_music.html', context)
    return render(request, 'core/upload_music.html', context)

#---------------------------------------------------------------------------------------------------------------------------------

from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from .models import UserProfile, Music, Follow
from django.contrib.auth.models import User

# This is a sample function for the user profile page.
# You need to adjust your existing view to match this pattern.
from django.shortcuts import render, get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.contrib.auth.models import User
from .models import Music, Follow

def user_profile(request, username):
    # Retrieve the user object and related data
    user_profile_user = get_object_or_404(User, username=username)
    uploaded_music = Music.objects.filter(uploaded_by=user_profile_user)
    follower_count = Follow.objects.filter(followed=user_profile_user).count()
    following_count = Follow.objects.filter(follower=user_profile_user).count()
    is_following = False

    if request.user.is_authenticated:
        is_following = Follow.objects.filter(follower=request.user, followed=user_profile_user).exists()
    
    context = {
        'user_profile': user_profile_user,
        'uploaded_music': uploaded_music,
        'follower_count': follower_count,
        'following_count': following_count,
        'is_following': is_following
    }

    # Check if the request is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Render ONLY the content block and return it as a simple HTTP response.
        # This prevents the duplicated navbars.
        html = render_to_string('core/user_profile.html', context, request=request)
        return HttpResponse(html)
    
    # For a standard, full page request, render the complete template.
    return render(request, 'core/user_profile.html', context)

#---------------------------------------------------------------------------------------------------------------------------------

@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)

    if request.user != user_to_follow:
        follow_instance, created = Follow.objects.get_or_create(
            follower=request.user,
            followed=user_to_follow
        )

        if created:
            Notification.objects.create(
                recipient=user_to_follow,
                sender=request.user,
                notification_type=Notification.NEW_FOLLOWER, 
                message=f'{request.user.username} started following you.'
            )
        else:
            follow_instance.delete()

    if is_ajax(request):
        follower_count = Follow.objects.filter(followed=user_to_follow).count()
        following_count = Follow.objects.filter(follower=user_to_follow).count()
        is_following = Follow.objects.filter(follower=request.user, followed=user_to_follow).exists()
        return render(request, 'core/user_profile_buttons.html', {
            'is_following': is_following,
            'user_profile': user_to_follow,
            'follower_count': follower_count,
            'following_count': following_count
        })
    
    return redirect('user_profile', username=user_to_follow.username) 

#---------------------------------------------------------------------------------------------------------------------------------

import json
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from .models import Music, UserProfile
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import UserProfileForm

# ... other imports and view functions ...

from django.db.models import Q
from .models import Music, UserProfile  # Import your UserProfile model

from django.db.models import Q
from django.shortcuts import render
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Music, UserProfile # Import your models

from django.db.models import Q
from django.shortcuts import render
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Music, UserProfile

def search(request):
    # Check for query in both GET and POST requests
    query = request.GET.get('q') or request.POST.get('query')

    music_results = []
    user_results = []

    if query:
        # Filter Music by title or artist (case-insensitive)
        music_results = Music.objects.filter(
            Q(title__icontains=query) | Q(artist__icontains=query)
        )
        
        # Filter UserProfile by related User's username (case-insensitive)
        user_results = UserProfile.objects.filter(
            Q(user__username__icontains=query)
        )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        music_html = render_to_string('core/music_results.html', {'music_results': music_results}, request=request)
        user_html = render_to_string('core/user_results.html', {'user_results': user_results}, request=request)
        return JsonResponse({
            'music_html': music_html,
            'user_html': user_html,
        })
    
    return render(request, 'core/search_results.html', {
        'music_results': music_results,
        'user_results': user_results,
        'query': query
    })

# ... rest of your views ...

#---------------------------------------------------------------------------------------------------------------------------------

def music_detail(request, pk):
    music = get_object_or_404(Music, id=pk)
    
    likes_count = music.likedislike_set.filter(is_like=True).count()
    dislikes_count = music.likedislike_set.filter(is_like=False).count()
    
    user_vote = None
    if request.user.is_authenticated:
        user_vote = music.likedislike_set.filter(user=request.user).first()
        
    context = {
        'music': music,
        'likes_count': likes_count,
        'dislikes_count': dislikes_count,
        'user_vote': user_vote,
    }
    
    if is_ajax(request):
        return render(request, 'core/music_detail.html', context)
    return render(request, 'core/music_detail.html', context)

#---------------------------------------------------------------------------------------------------------------------------------

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('homepage')
    else:
        form = CustomUserCreationForm()
    
    context = {'form': form}
    if is_ajax(request):
        return render(request, 'core/signup.html', context)
    return render(request, 'core/signup.html', context)

#---------------------------------------------------------------------------------------------------------------------------------

def user_logout(request):
    logout(request)
    return redirect('homepage')

#---------------------------------------------------------------------------------------------------------------------------------

@login_required
def like_music(request, pk):
    music = get_object_or_404(Music, pk=pk)
    
    existing_vote, created = LikeDislike.objects.get_or_create(user=request.user, music=music)
    
    send_notification = False

    if not created: 
        if existing_vote.is_like: 
            existing_vote.delete()
        else: 
            existing_vote.is_like = True
            existing_vote.save()
            send_notification = True 
    else: 
        existing_vote.is_like = True 
        existing_vote.save() 
        send_notification = True 

    if send_notification and request.user != music.uploaded_by:
        Notification.objects.create(
            recipient=music.uploaded_by,
            sender=request.user,
            notification_type='like',
            message=f'{request.user.username} liked your music: {music.title}.'
        )

    if is_ajax(request):
        likes_count = music.likedislike_set.filter(is_like=True).count()
        dislikes_count = music.likedislike_set.filter(is_like=False).count()
        user_vote = music.likedislike_set.filter(user=request.user).first()
        return render(request, 'core/music_like_dislike.html', {
            'music': music,
            'likes_count': likes_count,
            'dislikes_count': dislikes_count,
            'user_vote': user_vote,
        })
    return redirect('homepage')

@login_required
def dislike_music(request, pk):
    music = get_object_or_404(Music, pk=pk)
    
    existing_vote, created = LikeDislike.objects.get_or_create(user=request.user, music=music)
    
    send_notification = False

    if not created: 
        if not existing_vote.is_like: 
            existing_vote.delete()
        else: 
            existing_vote.is_like = False
            existing_vote.save()
            send_notification = True 
    else: 
        existing_vote.is_like = False 
        existing_vote.save() 
        send_notification = True 

    if send_notification and request.user != music.uploaded_by:
        Notification.objects.create(
            recipient=music.uploaded_by,
            sender=request.user,
            notification_type='dislike',
            message=f'{request.user.username} disliked your music: {music.title}.'
        )

    if is_ajax(request):
        likes_count = music.likedislike_set.filter(is_like=True).count()
        dislikes_count = music.likedislike_set.filter(is_like=False).count()
        user_vote = music.likedislike_set.filter(user=request.user).first()
        return render(request, 'core/music_like_dislike.html', {
            'music': music,
            'likes_count': likes_count,
            'dislikes_count': dislikes_count,
            'user_vote': user_vote,
        })
    return redirect('homepage')
    
#---------------------------------------------------------------------------------------------------------------------------------

@login_required
def add_comment(request, pk):
    if request.method == 'POST':
        music = get_object_or_404(Music, pk=pk)
        comment_content = request.POST.get('comment_text')
        
        if comment_content:
            Comment.objects.create(user=request.user, music=music, content=comment_content)
            
            if request.user != music.uploaded_by:
                Notification.objects.create(
                    recipient=music.uploaded_by,
                    sender=request.user,
                    notification_type='comment',
                    message=f'{request.user.username} commented on your music: {music.title}.'
                )
        
    return redirect(request.META.get('HTTP_REFERER', 'homepage'))

#---------------------------------------------------------------------------------------------------------------------------------

@login_required
def notifications(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    context = {
        'notifications': notifications
    }
    
    if is_ajax(request):
        return render(request, 'core/notifications.html', context)
    return render(request, 'core/notifications.html', context)

#---------------------------------------------------------------------------------------------------------------------------------

@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'notifications'))

#---------------------------------------------------------------------------------------------------------------------------------

from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from .models import User, UserProfile
from .forms import UserProfileForm
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.urls import reverse

def is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'

from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from .forms import UserProfileForm

def edit_profile(request, username):
    user_to_edit = get_object_or_404(User, username=username)

    # Ensure the logged-in user can only edit their own profile
    if request.user != user_to_edit:
        return HttpResponse("You are not authorized to view this page.", status=403)
        
    profile_form = UserProfileForm(instance=user_to_edit.userprofile)

    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_to_edit.userprofile)
        if profile_form.is_valid():
            profile_form.save()
            # Redirect to the user's profile page after saving
            return redirect('user_profile', username=user_to_edit.username)
        
    context = {'user_to_edit': user_to_edit, 'profile_form': profile_form}
    
    # Check if the request is an AJAX request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Render ONLY the content block for AJAX and return it
        html = render_to_string('core/edit_profile.html', context, request=request)
        return HttpResponse(html)
    
    # For a standard request, render the full page
    return render(request, 'core/edit_profile.html', context)


#---------------------------------------------------------------------------------------------------------------------------------

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@require_POST
def save_player_state_api(request):
    if request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            song_id = data.get('song_id')
            position = data.get('position')
            
            user_profile = request.user.userprofile
            user_profile.last_played_song_id = song_id
            user_profile.playback_position = position
            user_profile.save()
            
            return JsonResponse({'status': 'success'})
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({'status': 'error', 'message': 'Invalid data'}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Not authenticated'}, status=401)