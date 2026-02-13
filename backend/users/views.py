from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from .models import CustomUser, UserProgress
from .forms import CustomUserCreationForm, LoginForm, UserProfileForm
from courses.models import Course, UserCourseProgress



def login_view(request):
    """Сторінка входу"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f'Вітаємо, {username}!')
                return redirect('home')
            else:
                messages.error(request, 'Невірний логін або пароль')
    else:
        form = LoginForm()
    
    return render(request, 'users/login.html', {'form': form})


def register_view(request):
    """Сторінка реєстрації"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Реєстрація успішна! Вітаємо, {user.username}!')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})


@login_required
def profile_view(request):
    """Сторінка профілю з можливістю редагування"""
    user = request.user
    progress = UserProgress.objects.get_or_create(user=user)[0]
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профіль успішно оновлено!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Помилка при оновленні профілю. Перевірте введені дані.')
    else:
        form = UserProfileForm(instance=user)
    
    completed_progress = UserCourseProgress.objects.filter(
        user=user, 
        is_completed=True
    ).select_related('course')
    
    completed_courses_count = completed_progress.count()

    # Розрахунок прогресу щоденної цілі
    daily_progress_percent = min(int((progress.daily_xp / progress.daily_goal) * 100), 100) if progress.daily_goal > 0 else 0
    remaining_xp = max(progress.daily_goal - progress.daily_xp, 0)

    context = {
        'user': user,
        'progress': progress,
        'form': form,
        'completed_courses_count': completed_courses_count,
        'completed_courses': completed_progress,
        'daily_progress_percent': daily_progress_percent,
        'remaining_xp': remaining_xp,
        'badges': user.badges.all().select_related('badge'),
    }

    return render(request, 'users/profile.html', context)


@login_required
def leaderboard_view(request):
    """Сторінка лідерборду"""
    # Отримуємо ТОП-10 користувачів за загальним XP
    top_users = UserProgress.objects.select_related('user').order_by('-total_xp')[:10]
    
    # Позиція поточного користувача
    user_rank = UserProgress.objects.filter(total_xp__gt=request.user.progress.total_xp).count() + 1
    
    context = {
        'top_users': top_users,
        'user_rank': user_rank,
    }
    return render(request, 'users/leaderboard.html', context)


def logout_view(request):
    """Вихід"""
    logout(request)
    return redirect('home')



class ProfileView(APIView):
    """Перегляд профілю користувача"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        progress = UserProgress.objects.get_or_create(user=user)[0]
        
        return Response({
            'username': user.username,
            'email': user.email,
            'native_language': user.native_language,
            'learning_language': user.learning_language,
            'level': user.level,
            'progress': {
                'total_lessons_completed': progress.total_lessons_completed,
                'total_exercises_completed': progress.total_exercises_completed,
                'current_streak': progress.current_streak,
                'total_xp': progress.total_xp,
            }
        })


class ProgressView(APIView):
    """Детальний перегляд прогресу"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        progress = UserProgress.objects.get_or_create(user=request.user)[0]
        
        return Response({
            'total_lessons_completed': progress.total_lessons_completed,
            'total_exercises_completed': progress.total_exercises_completed,
            'current_streak': progress.current_streak,
            'longest_streak': progress.longest_streak,
            'total_xp': progress.total_xp,
            'last_activity_date': progress.last_activity_date,
        })
