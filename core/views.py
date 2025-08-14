from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.db.models import Q
from django.urls import reverse


from .forms import CustomUserCreationForm, MusicUploadForm, UserProfileForm

from .models import Music, User, Follow, LikeDislike, Comment, Notification, UserProfile
from .forms import MusicUploadForm
#---------------------------------------------------------------------------------------------------------------------------------





from django.shortcuts import render
from django.db.models import Q
from .models import Music, Follow, User, LikeDislike, Comment



from django.db.models import Count, Q
from django.shortcuts import render
from .models import Music, Follow, User, Comment, LikeDislike, Notification 





def homepage(request):
    
    music_list = Music.objects.all().order_by('-uploaded_at').prefetch_related(
        'comments__user'
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
        ).order_by('?')[:5]
    
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

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import MusicUploadForm 
from .models import Follow, Notification, User 

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
            
            return redirect('homepage')
    else:
        form = MusicUploadForm()
        
    return render(request, 'core/upload_music.html', {'form': form})


#---------------------------------------------------------------------------------------------------------------------------------


from django.shortcuts import render, get_object_or_404
from .models import Music, Follow, User, UserProfile 

def user_profile(request, username):
    
    user_to_view = get_object_or_404(User, username=username)

    
    music_list = Music.objects.filter(uploaded_by=user_to_view)

    is_following = False
    if request.user.is_authenticated:
        
        is_following = Follow.objects.filter(follower=request.user, followed=user_to_view).exists()

    
    follower_count = Follow.objects.filter(followed=user_to_view).count()
    following_count = Follow.objects.filter(follower=user_to_view).count()

    context = {
        'user_profile': user_to_view, 
        'uploaded_music': music_list,
        'is_following': is_following,
        'follower_count': follower_count,
        'following_count': following_count,
    }
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

    return redirect('user_profile', username=user_to_follow.username) 

#---------------------------------------------------------------------------------------------------------------------------------

def search(request):
    query = request.GET.get('q')
    music_results = Music.objects.filter(Q(title__icontains=query) | Q(artist__icontains=query))
    user_results = User.objects.filter(Q(username__icontains=query))
    return render(request, 'core/search_results.html', {'query': query, 'music_results': music_results, 'user_results': user_results})

#---------------------------------------------------------------------------------------------------------------------------------

def music_detail(request, pk):
    
    music = get_object_or_404(Music, id=pk)

    
    likes_count = music.votes.filter(vote_type='L').count()
    dislikes_count = music.votes.filter(vote_type='D').count()
    
    
    user_vote = None
    if request.user.is_authenticated:
        user_vote = music.votes.filter(user=request.user).first()
        
    context = {
        'music': music,
        'likes_count': likes_count,
        'dislikes_count': dislikes_count,
        'user_vote': user_vote,
    }
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
    return render(request, 'core/signup.html', {'form': form})

#---------------------------------------------------------------------------------------------------------------------------------

def user_logout(request):
    logout(request)
    return redirect('login')

#---------------------------------------------------------------------------------------------------------------------------------



from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Music, LikeDislike, Notification

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

    # Create a notification for the music uploader
    if send_notification and request.user != music.uploaded_by:
        Notification.objects.create(
            recipient=music.uploaded_by,
            sender=request.user,
            notification_type='like',
             
            message=f'{request.user.username} liked your music: {music.title}.'
        )

    # Redirect to the previous page or homepage
    return redirect(request.META.get('HTTP_REFERER', 'homepage'))




from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Music, LikeDislike, Notification 

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

    return redirect(request.META.get('HTTP_REFERER', 'homepage'))
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
    return render(request, 'core/notifications.html', context)

#---------------------------------------------------------------------------------------------------------------------------------

@login_required
def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'notifications'))

#---------------------------------------------------------------------------------------------------------------------------------

@login_required
def edit_profile(request, username):
    user = get_object_or_404(User, username=username)

    if request.user != user:
        return redirect('user_profile', username=user.username)
        
    user_profile, created = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            return redirect('user_profile', username=user.username)
    else:
        form = UserProfileForm(instance=user_profile)
    
    context = {'form': form, 'user_to_edit': user}
    return render(request, 'core/edit_profile.html', context)

from django.shortcuts import render
from django.db.models import Q
from .models import Music, User

def search_results(request):
    query = request.GET.get('q') 
    music_results = []
    user_results = []

    if query:
        
        music_results = Music.objects.filter(
            Q(title__icontains=query) | Q(artist__icontains=query)
        )
        
        # Search for users by username
        user_results = User.objects.filter(username__icontains=query)
    
    context = {
        'query': query,
        'music_results': music_results,
        'user_results': user_results,
    }
    return render(request, 'core/search_results.html', context)

