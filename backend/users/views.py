import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.timezone import localdate, make_aware, now

from courses.models import Course, UserCourseProgress
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import CustomUserCreationForm, LoginForm, UserProfileForm
from .models import CustomUser, UserProgress
from .services import get_missions_status


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                messages.success(request, f"Вітаємо, {username}!")
                return redirect("home")
            else:
                messages.error(request, "Невірний логін або пароль")
    else:
        form = LoginForm()

    return render(request, "users/login.html", {"form": form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            messages.success(request, f"Реєстрація успішна! Вітаємо, {user.username}!")
            return redirect("home")
    else:
        form = CustomUserCreationForm()

    return render(request, "users/register.html", {"form": form})


@login_required
def profile_view(request):
    user = request.user
    progress = UserProgress.objects.get_or_create(user=user)[0]

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профіль успішно оновлено!")
            return redirect("users:profile")
        else:
            messages.error(
                request, "Помилка при оновленні профілю. Перевірте введені дані."
            )
    else:
        form = UserProfileForm(instance=user)

    completed_progress = UserCourseProgress.objects.filter(
        user=user, is_completed=True
    ).select_related("course")

    from tests.models import TestAttempt

    completed_tests = TestAttempt.objects.filter(
        user=user, status="completed"
    ).select_related("test")

    completed_courses_count = completed_progress.count() + completed_tests.count()

    daily_progress_percent = (
        min(int((progress.daily_xp / progress.daily_goal) * 100), 100)
        if progress.daily_goal > 0
        else 0
    )
    remaining_xp = max(progress.daily_goal - progress.daily_xp, 0)

    from courses.models import Exercise

    failed_mistakes_count = (
        Exercise.objects.filter(attempts__user=user, attempts__is_correct=False)
        .exclude(attempts__user=user, attempts__is_correct=True)
        .distinct()
        .count()
    )

    context = {
        "user": user,
        "progress": progress,
        "form": form,
        "completed_courses_count": completed_courses_count,
        "completed_courses": completed_progress,
        "completed_tests": completed_tests,
        "daily_progress_percent": daily_progress_percent,
        "remaining_xp": remaining_xp,
        "badges": user.badges.all().select_related("badge"),
        "failed_mistakes_count": failed_mistakes_count,
    }

    return render(request, "users/profile.html", context)


@login_required
def missions_view(request):
    user = request.user
    progress = getattr(user, "progress", None)

    if not progress:
        from .models import UserProgress

        progress = UserProgress.objects.create(user=user)

    today = localdate()
    current_time = now()
    start_of_day = make_aware(datetime.datetime.combine(today, datetime.time.min))
    end_of_day = make_aware(datetime.datetime.combine(today, datetime.time.max))

    # Seconds until midnight (for countdown)
    import datetime

    midnight = datetime.datetime.combine(
        today + datetime.timedelta(days=1), datetime.time.min
    )
    from django.utils import timezone

    midnight = (
        timezone.make_aware(midnight) if timezone.is_naive(midnight) else midnight
    )
    seconds_until_reset = max(0, int((midnight - current_time).total_seconds()))

    # Get statuses from central service
    statuses = get_missions_status(user)

    # ── Mission 1: Daily XP ──────────────────────────────────────────
    xp_goal = progress.daily_goal
    xp_current = progress.daily_xp
    xp_percent = min(int((xp_current / xp_goal) * 100), 100) if xp_goal > 0 else 0
    xp_completed = statuses["daily_xp"]

    # ── Mission 2: Streak ────────────────────────────────────────────
    streak_completed = statuses["streak"]
    streak_percent = 100 if streak_completed else 0

    # ── Mission 3: Lessons ───────────────────────────────────────────
    from courses.models import Exercise
    from tests.models import TestAttempt

    lessons_today_goal = 3
    lessons_today_current = min(
        TestAttempt.objects.filter(
            user=user,
            completed_at__range=(start_of_day, end_of_day),
            status="completed",
        ).count(),
        lessons_today_goal,
    )
    lessons_percent = min(int((lessons_today_current / lessons_today_goal) * 100), 100)
    lessons_completed = statuses["lessons"]

    # ── Mission 4: Exercises (Course Exercises + Test Questions) ─────
    exercises_goal = 10
    from courses.models import UserExerciseAttempt
    from tests.models import TestAnswer

    course_ex_today = (
        UserExerciseAttempt.objects.filter(
            user=user, attempted_at__range=(start_of_day, end_of_day), is_correct=True
        )
        .values("exercise")
        .distinct()
        .count()
    )

    test_ex_today = (
        TestAnswer.objects.filter(
            attempt__user=user,
            attempt__completed_at__range=(start_of_day, end_of_day),
            is_correct=True,
        )
        .values("question")
        .distinct()
        .count()
    )

    exercises_today_total = course_ex_today + test_ex_today
    exercises_current = min(exercises_today_total, exercises_goal)
    exercises_percent = min(int((exercises_current / exercises_goal) * 100), 100)
    exercises_completed = statuses["exercises"]

    # ── Mission 5: Mistakes Fix ──────────────────────────────────────
    failed_mistakes_count = (
        Exercise.objects.filter(
            attempts__user=user,
            attempts__is_correct=False,
        )
        .exclude(
            attempts__user=user,
            attempts__is_correct=True,
        )
        .distinct()
        .count()
    )
    mistakes_completed = statuses["mistakes"]
    mistakes_percent = (
        100
        if mistakes_completed
        else max(
            0,
            min(
                int(
                    100 - (failed_mistakes_count / max(failed_mistakes_count, 1)) * 100
                ),
                99,
            ),
        )
    )

    # ── Bonus mission: Big XP day ────────────────────
    bonus_xp_goal = progress.daily_goal * 3
    bonus_current = min(xp_current, bonus_xp_goal)
    bonus_percent = min(int((bonus_current / bonus_xp_goal) * 100), 100)
    bonus_completed = statuses["bonus"]

    missions = [
        {
            "id": "daily_xp",
            "icon": "fa-star",
            "gradient": "linear-gradient(135deg, #f59e0b, #f97316)",
            "title": "Денна норма",
            "desc": f"Набери {xp_goal} XP сьогодні. Пройди урок або тест.",
            "current": xp_current,
            "goal": xp_goal,
            "current_label": f"{xp_current} XP",
            "goal_label": f"{xp_goal} XP",
            "percent": xp_percent,
            "completed": xp_completed,
            "reward_xp": 15,
            "difficulty": "normal",
            "difficulty_label": "Щоденна",
            "link": "/courses/",
            "link_label": "Відкрити курси",
        },
        {
            "id": "streak",
            "icon": "fa-fire",
            "gradient": "linear-gradient(135deg, #ef4444, #f97316)",
            "title": "Серія днів",
            "desc": f"Зайдись сьогодні — серія не перервалась. Поточна: {progress.current_streak} д.",
            "current": 1 if streak_completed else 0,
            "goal": 1,
            "current_label": "Виконано" if streak_completed else "Не зараховано",
            "goal_label": "Сьогодні",
            "percent": streak_percent,
            "completed": streak_completed,
            "reward_xp": 10,
            "difficulty": "easy",
            "difficulty_label": "Легка",
            "link": "/courses/",
            "link_label": "Займатися зараз",
        },
        {
            "id": "lessons",
            "icon": "fa-book-open",
            "gradient": "linear-gradient(135deg, #8b5cf6, #6366f1)",
            "title": "Тестовий день",
            "desc": f"Пройди {lessons_today_goal} тести сьогодні.",
            "current": lessons_today_current,
            "goal": lessons_today_goal,
            "current_label": f"{lessons_today_current}/{lessons_today_goal}",
            "goal_label": f"{lessons_today_goal} тести",
            "percent": lessons_percent,
            "completed": lessons_completed,
            "reward_xp": 20,
            "difficulty": "hard",
            "difficulty_label": "Складна",
            "link": "/tests/",
            "link_label": "До тестів",
        },
        {
            "id": "exercises",
            "icon": "fa-dumbbell",
            "gradient": "linear-gradient(135deg, #06b6d4, #3b82f6)",
            "title": "Вправи дня",
            "desc": f"Виконай {exercises_goal} вправ у будь-якому курсі.",
            "current": exercises_current,
            "goal": exercises_goal,
            "current_label": f"{exercises_current}/{exercises_goal}",
            "goal_label": f"{exercises_goal} вправ",
            "percent": exercises_percent,
            "completed": exercises_completed,
            "reward_xp": 25,
            "difficulty": "normal",
            "difficulty_label": "Звичайна",
            "link": "/courses/",
            "link_label": "Виконувати вправи",
        },
        {
            "id": "mistakes",
            "icon": "fa-bullseye",
            "gradient": "linear-gradient(135deg, #10b981, #059669)",
            "title": "Чисто",
            "desc": (
                f"Поверни і відпрацюй вправи, де помилився ({failed_mistakes_count} шт)."
                if not mistakes_completed
                else "Усі помилки виправлено."
            ),
            "current": (
                f"{failed_mistakes_count} лишилось"
                if not mistakes_completed
                else "Готово"
            ),
            "goal": "0 помилок",
            "current_label": (
                "0 помилок 🎉"
                if mistakes_completed
                else f"{failed_mistakes_count} помилок"
            ),
            "goal_label": "Виправити все",
            "percent": mistakes_percent,
            "completed": mistakes_completed,
            "reward_xp": 30,
            "difficulty": "hard",
            "difficulty_label": "Складна",
            "link": "/courses/mistakes/",
            "link_label": "Виправляти помилки",
        },
        {
            "id": "bonus",
            "icon": "fa-crown",
            "gradient": "linear-gradient(135deg, #fbbf24, #ec4899)",
            "title": "Максимальний день",
            "desc": f"Набери {bonus_xp_goal} XP за один день — важко, але реально.",
            "current": bonus_current,
            "goal": bonus_xp_goal,
            "current_label": f"{bonus_current} XP",
            "goal_label": f"{bonus_xp_goal} XP",
            "percent": bonus_percent,
            "completed": bonus_completed,
            "reward_xp": 50,
            "difficulty": "bonus",
            "difficulty_label": "🏆 Бонус",
            "link": "/courses/",
            "link_label": "Прийняти виклик",
        },
    ]

    completed_count = sum(1 for m in missions if m["completed"])
    total_count = len(missions)
    total_possible_xp = sum(m["reward_xp"] for m in missions)
    earned_xp = sum(m["reward_xp"] for m in missions if m["completed"])

    context = {
        "missions": missions,
        "completed_count": completed_count,
        "total_count": total_count,
        "all_completed": completed_count == total_count,
        "total_possible_xp": total_possible_xp,
        "earned_xp": earned_xp,
        "seconds_until_reset": seconds_until_reset,
        "current_streak": progress.current_streak,
    }
    return render(request, "users/missions.html", context)


def logout_view(request):
    logout(request)
    return redirect("home")


class ProfileView(APIView):
    """Перегляд профілю користувача"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        progress = UserProgress.objects.get_or_create(user=user)[0]

        return Response(
            {
                "username": user.username,
                "email": user.email,
                "native_language": user.native_language,
                "learning_language": user.learning_language,
                "level": user.level,
                "progress": {
                    "total_lessons_completed": progress.total_lessons_completed,
                    "total_exercises_completed": progress.total_exercises_completed,
                    "current_streak": progress.current_streak,
                    "total_xp": progress.total_xp,
                },
            }
        )


class ProgressView(APIView):
    """Детальний перегляд прогресу"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        progress = UserProgress.objects.get_or_create(user=request.user)[0]

        return Response(
            {
                "total_lessons_completed": progress.total_lessons_completed,
                "total_exercises_completed": progress.total_exercises_completed,
                "current_streak": progress.current_streak,
                "longest_streak": progress.longest_streak,
                "total_xp": progress.total_xp,
                "last_activity_date": progress.last_activity_date,
            }
        )
