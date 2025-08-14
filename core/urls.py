from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Homepage and Authentication
    path('', views.homepage, name='homepage'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('search/', views.search_results, name='search_results'),
    # Profile and Follow System
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('follow/<str:username>/', views.follow_user, name='follow_user'),
    path('edit_profile/<str:username>/', views.edit_profile, name='edit_profile'),

    # Music Upload and Details
    path('upload/', views.upload_music, name='upload_music'),
    path('music/<int:pk>/', views.music_detail, name='music_detail'),

    # Interactions
    path('music/<int:pk>/like/', views.like_music, name='like_music'),
    path('music/<int:pk>/dislike/', views.dislike_music, name='dislike_music'),
    path('music/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    # Notifications and Search
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('search/', views.search, name='search'),
]