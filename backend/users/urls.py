from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.profile_view, name='profile'),
    path('leaderboard/', views.leaderboard_view, name='leaderboard'),
    path('logout/', views.logout_view, name='logout'),
    path('api/profile/', views.ProfileView.as_view(), name='api-profile'),
    path('api/progress/', views.ProgressView.as_view(), name='api-progress'),
]
