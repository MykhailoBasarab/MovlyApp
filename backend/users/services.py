import datetime

from django.contrib import messages
from django.utils.timezone import localdate, make_aware, now

from courses.models import Exercise, UserExerciseAttempt
from tests.models import TestAnswer, TestAttempt

from .models import UserProgress


def get_missions_status(user):
    """
    Returns a dictionary of mission statuses for the given user.
    Keys are mission IDs, values are Boolean (True if completed).
    """
    progress = getattr(user, "progress", None)
    if not progress:
        return {}

    today = localdate()
    start_of_day = make_aware(datetime.datetime.combine(today, datetime.time.min))
    end_of_day = make_aware(datetime.datetime.combine(today, datetime.time.max))

    # Mission 1: Daily XP
    xp_completed = progress.daily_xp >= progress.daily_goal

    # Mission 2: Streak
    streak_completed = progress.last_activity_date == today

    # Mission 3: Lessons (Tests)
    lessons_today_current = TestAttempt.objects.filter(
        user=user,
        completed_at__range=(start_of_day, end_of_day),
        status="completed",
    ).count()
    lessons_completed = lessons_today_current >= 3

    # Mission 4: Exercises (Count unique correct exercises + test answers today)
    # Course Exercises
    course_ex_today = (
        UserExerciseAttempt.objects.filter(
            user=user, attempted_at__range=(start_of_day, end_of_day), is_correct=True
        )
        .values("exercise")
        .distinct()
        .count()
    )

    # Test Questions
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
    exercises_completed = exercises_today_total >= 10

    # Mission 5: Mistakes Fix
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
    mistakes_completed = failed_mistakes_count == 0

    # Bonus mission: Big XP day
    bonus_xp_goal = progress.daily_goal * 3
    bonus_completed = progress.daily_xp >= bonus_xp_goal

    return {
        "daily_xp": xp_completed,
        "streak": streak_completed,
        "lessons": lessons_completed,
        "exercises": exercises_completed,
        "mistakes": mistakes_completed,
        "bonus": bonus_completed,
    }


def check_mission_completions(request, before_statuses):
    """
    Compares current mission statuses with before_statuses and adds messages for new completions.
    """
    from .models import Notification
    current_statuses = get_missions_status(request.user)

    mission_names = {
        "daily_xp": "Денна норма XP",
        "streak": "Серія днів",
        "lessons": "Тестовий день",
        "exercises": "Вправи дня",
        "mistakes": "Робота над помилками",
        "bonus": "Максимальний день (БОНУС)",
    }

    for mission_id, is_completed in current_statuses.items():
        if is_completed and not before_statuses.get(mission_id, False):
            # Mission was just completed!
            name = mission_names.get(mission_id, mission_id)
            messages.info(request, f"🎉 Місія виконана: {name}!")
            
            # Create persistent notification
            from django.urls import reverse
            Notification.objects.create(
                user=request.user,
                title="Місія виконана! 🎯",
                message=f"Ви успішно виконали місію: {name}",
                notification_type='success',
                link=reverse("users:missions")
            )

    return current_statuses
