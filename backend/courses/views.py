from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from ai_services.services import AIExerciseService
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from tests.models import Test, TestAttempt
from users.models import Badge, UserBadge, UserProgress
from users.services import check_mission_completions, get_missions_status

from .forms import ExerciseAnswerForm, FilterForm, MultipleChoiceForm
from .models import (
    Course,
    CourseTest,
    Exercise,
    Lesson,
    UserCourseProgress,
    UserExerciseAttempt,
    UserLessonProgress,
)


@login_required
def mistakes_list_view(request):
    """Стовпчик роботи над помилками: вправи, які користувач виконав неправильно і ще не виправив"""
    user = request.user

    # Знаходимо вправи, де була хоча б одна помилка, і жодної правильної відповіді
    failed_exercises = (
        Exercise.objects.filter(attempts__user=user, attempts__is_correct=False)
        .exclude(attempts__user=user, attempts__is_correct=True)
        .distinct()
        .select_related(
            "lesson", "lesson__course", "course_test", "course_test__course"
        )
        .order_by("lesson__course", "order")
    )

    from django.urls import reverse

    # Останні спроби та джерела для кожної помилки
    for ex in failed_exercises:
        ex.last_attempt = (
            UserExerciseAttempt.objects.filter(user=user, exercise=ex)
            .order_by("-attempted_at")
            .first()
        )

        if ex.lesson:
            ex.source_name = ex.lesson.title
            ex.source_url = reverse(
                "courses:lesson-detail", kwargs={"pk": ex.lesson.id}
            )
            ex.source_type = "УРОК"
        elif ex.course_test:
            ex.source_name = ex.course_test.course.title
            ex.source_url = reverse(
                "courses:course-detail", kwargs={"pk": ex.course_test.course.id}
            )
            ex.source_type = "ТЕСТ"
        else:
            ex.source_name = "Додатково"
            ex.source_url = "#"
            ex.source_type = "Вправа"

    context = {
        "failed_exercises": failed_exercises,
        "total_mistakes": failed_exercises.count(),
    }
    return render(request, "courses/mistakes.html", context)


def home_view(request):
    recommended_courses = []
    recommended_tests = []

    if request.user.is_authenticated:
        user = request.user
        recommended_courses = Course.objects.filter(
            language=user.learning_language, level=user.level, is_active=True
        ).exclude(user_progress__user=user, user_progress__is_completed=True)[:3]

        if not recommended_courses.exists():
            recommended_courses = Course.objects.filter(
                language=user.learning_language, is_active=True
            ).exclude(user_progress__user=user, user_progress__is_completed=True)[:3]

        recommended_tests = Test.objects.filter(
            language=user.learning_language, level=user.level, is_active=True
        ).exclude(attempts__user=user, attempts__status="completed")[:3]

        if not recommended_tests.exists():
            recommended_tests = Test.objects.filter(
                language=user.learning_language, is_active=True
            ).exclude(attempts__user=user, attempts__status="completed")[:3]

    context = {
        "recommended_courses": recommended_courses,
        "recommended_tests": recommended_tests,
    }
    return render(request, "home.html", context)


def courses_list_view(request):
    form = FilterForm(request.GET)
    courses = (
        Course.objects.filter(is_active=True)
        .exclude(language="pl")
        .order_by("language")
    )

    if form.is_valid():
        language = form.cleaned_data.get("language")
        level = form.cleaned_data.get("level")

        if language:
            courses = courses.filter(language=language)
        if level:
            courses = courses.filter(level=level)

    completed_courses_ids = set()
    if request.user.is_authenticated:

        completed_via_test = UserCourseProgress.objects.filter(
            user=request.user, is_completed=True
        ).values_list("course_id", flat=True)
        completed_courses_ids.update(completed_via_test)

        courses_with_counts = courses.annotate(
            total_lessons=Count("lessons", filter=Q(lessons__is_active=True))
        )
        lesson_counts = {c.id: c.total_lessons for c in courses_with_counts}

        user_completed_lessons = (
            UserLessonProgress.objects.filter(
                user=request.user,
                is_completed=True,
                lesson__course__in=courses,
                lesson__is_active=True,
            )
            .values("lesson__course_id")
            .annotate(completed_count=Count("id"))
        )

        for item in user_completed_lessons:
            c_id = item["lesson__course_id"]
            if c_id in lesson_counts and lesson_counts[c_id] > 0:
                if item["completed_count"] >= lesson_counts[c_id]:
                    completed_courses_ids.add(c_id)

    started_courses_ids = set()
    if request.user.is_authenticated:

        started_via_course = UserCourseProgress.objects.filter(
            user=request.user
        ).values_list("course_id", flat=True)
        started_courses_ids.update(started_via_course)

        started_via_lessons = (
            UserLessonProgress.objects.filter(
                user=request.user, lesson__course__in=courses
            )
            .values_list("lesson__course_id", flat=True)
            .distinct()
        )
        started_courses_ids.update(started_via_lessons)

        started_via_exercises = (
            UserExerciseAttempt.objects.filter(
                user=request.user, exercise__lesson__course__in=courses
            )
            .values_list("exercise__lesson__course_id", flat=True)
            .distinct()
        )
        started_courses_ids.update(started_via_exercises)

    context = {
        "courses": courses,
        "form": form,
        "completed_courses_ids": completed_courses_ids,
        "started_courses_ids": started_courses_ids,
    }
    return render(request, "courses/list.html", context)


def course_detail_view(request, pk):
    course = get_object_or_404(Course, pk=pk, is_active=True)
    lessons = course.lessons.filter(is_active=True).order_by("order")

    user_progress = {}
    if request.user.is_authenticated:
        progress_list = UserLessonProgress.objects.filter(
            user=request.user, lesson__in=lessons
        )
        for progress in progress_list:
            user_progress[progress.lesson.id] = progress

    user_course_progress = None
    can_take_test = False
    completed_lessons_count = 0

    if request.user.is_authenticated:
        user_course_progress = UserCourseProgress.objects.filter(
            user=request.user, course=course
        ).first()

        completed_lessons_count = UserLessonProgress.objects.filter(
            user=request.user, lesson__course=course, is_completed=True
        ).count()

        if completed_lessons_count >= lessons.count() and lessons.count() > 0:
            can_take_test = True

    context = {
        "course": course,
        "lessons": lessons,
        "user_progress": user_progress,
        "user_course_progress": user_course_progress,
        "has_test": hasattr(course, "final_test"),
        "can_take_test": can_take_test,
        "completed_lessons_count": completed_lessons_count,
        "total_lessons_count": lessons.count(),
    }
    return render(request, "courses/detail.html", context)


@login_required
def lesson_detail_view(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk, is_active=True)
    exercises = lesson.exercises.all().order_by("order")

    user_progress = UserLessonProgress.objects.filter(
        user=request.user, lesson=lesson
    ).first()

    attempts = {}
    completed_count = 0
    if request.user.is_authenticated:
        for exercise in exercises:
            attempt = UserExerciseAttempt.objects.filter(
                user=request.user, exercise=exercise, is_correct=True
            ).first()
            if attempt:
                attempts[exercise.id] = attempt
                completed_count += 1
            else:
                last_attempt = (
                    UserExerciseAttempt.objects.filter(
                        user=request.user, exercise=exercise
                    )
                    .order_by("-attempted_at")
                    .first()
                )
                if last_attempt:
                    attempts[exercise.id] = last_attempt

    feedback_ex = request.GET.get("feedback_ex")
    feedback_ex_id = 0
    if feedback_ex and feedback_ex.isdigit():
        feedback_ex_id = int(feedback_ex)

    context = {
        "lesson": lesson,
        "exercises": exercises,
        "user_progress": user_progress,
        "attempts": attempts,
        "completed_count": completed_count,
        "feedback_ex_id": feedback_ex_id,
    }
    return render(request, "courses/lesson.html", context)


@login_required
def submit_exercise_view(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk)

    if exercise.exercise_type == "multiple_choice" and exercise.options:
        form = MultipleChoiceForm(request.POST, options=exercise.options)
    else:
        form = ExerciseAnswerForm(request.POST)

    if form.is_valid():
        user_answer = form.cleaned_data.get("answer") or form.cleaned_data.get(
            "option", ""
        )
        ai_service = None
        is_correct = False

        # Для вправ курсів використовуємо ручне порівняння
        correct = exercise.correct_answer.strip().lower()
        user = user_answer.strip().lower()

        if exercise.exercise_type == "multiple_choice":
            is_correct = correct == user
        elif exercise.exercise_type == "fill_blank":
            # Більш гнучке порівняння для пропусків
            is_correct = correct == user or correct in user
        else:
            is_correct = correct == user

        points_earned = exercise.points if is_correct else 0

        UserExerciseAttempt.objects.create(
            user=request.user,
            exercise=exercise,
            user_answer=user_answer,
            is_correct=is_correct,
            ai_feedback=None,
            points_earned=points_earned,
        )

        user_progress, _ = UserProgress.objects.get_or_create(user=request.user)

        is_ajax = (
            request.headers.get("x-requested-with") == "XMLHttpRequest"
            or request.GET.get("ajax") == "1"
        )

        if is_correct:

            count_correct = UserExerciseAttempt.objects.filter(
                user=request.user, exercise=exercise, is_correct=True
            ).count()

            if count_correct <= 1:  # Це перша правильна спроба
                # Check missions
                before_missions = get_missions_status(request.user)

                leveled_up = user_progress.add_xp(points_earned)
                user_progress.total_exercises_completed += 1
                user_progress.save()

                check_mission_completions(request, before_missions)

                if not is_ajax:
                    if leveled_up:
                        messages.info(
                            request, f"Вітаємо! Ви досягли рівня {user_progress.level}!"
                        )
                    messages.success(
                        request, f"Правильно! Ви отримали {points_earned} балів."
                    )
            else:
                if not is_ajax:
                    messages.success(
                        request, "Правильно! (Ви вже виконували цю вправу раніше)"
                    )
        else:
            if not is_ajax:
                messages.error(request, "Неправильно. Спробуйте ще раз!")

        if is_ajax:
            return JsonResponse(
                {
                    "success": True,
                    "is_correct": is_correct,
                    "points_earned": points_earned,
                    "user_answer": user_answer,
                    "correct_answer": exercise.correct_answer,
                }
            )

        return redirect(
            reverse("courses:lesson-detail", kwargs={"pk": exercise.lesson.id})
            + f"?feedback_ex={exercise.id}"
        )

    if (
        request.headers.get("x-requested-with") == "XMLHttpRequest"
        or request.GET.get("ajax") == "1"
    ):
        return JsonResponse(
            {"success": False, "error": "Помилка при відправці відповіді"}, status=400
        )

    messages.error(request, "Помилка при відправці відповіді")
    return redirect(
        reverse("courses:lesson-detail", kwargs={"pk": exercise.lesson.id})
        + f"?feedback_ex={exercise.id}"
    )


@login_required
def complete_lesson_view(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    user = request.user

    exercises = lesson.exercises.all()
    attempts = UserExerciseAttempt.objects.filter(user=user, exercise__in=exercises)

    if not attempts.exists():
        messages.warning(request, "Спочатку виконайте хоча б одну вправу")
        return redirect("courses:lesson-detail", pk=pk)

    total_points = sum(ex.points for ex in exercises)

    earned_points = 0
    for exercise in exercises:

        best_attempt = (
            UserExerciseAttempt.objects.filter(user=user, exercise=exercise)
            .order_by("-points_earned", "-attempted_at")
            .first()
        )

        if best_attempt:
            earned_points += best_attempt.points_earned

    score = int((earned_points / total_points) * 100) if total_points > 0 else 0

    progress, created = UserLessonProgress.objects.get_or_create(
        user=user, lesson=lesson
    )

    if not progress.is_completed:
        progress.is_completed = True
        progress.score = score
        progress.completed_at = timezone.now()
        progress.save()

        user_progress, _ = UserProgress.objects.get_or_create(user=user)

        # Check missions
        before_missions = get_missions_status(user)

        leveled_up = user_progress.add_xp(earned_points)
        user_progress.total_lessons_completed += 1
        user_progress.save()

        check_mission_completions(request, before_missions)

        total_lessons = lesson.course.lessons.filter(is_active=True).count()
        completed_lessons = UserLessonProgress.objects.filter(
            user=user, lesson__course=lesson.course, is_completed=True
        ).count()

        if completed_lessons >= total_lessons:
            course_progress, _ = UserCourseProgress.objects.get_or_create(
                user=user, course=lesson.course
            )
            if not course_progress.is_completed:
                course_progress.is_completed = True
                course_progress.completed_at = timezone.now()
                course_progress.save()

                course_badge = Badge.objects.filter(
                    criteria_type="course_completed", criteria_value=lesson.course.id
                ).first()
                if course_badge:
                    UserBadge.objects.get_or_create(user=user, badge=course_badge)
                    
                    from django.urls import reverse
                    from users.models import Notification
                    Notification.objects.create(
                        user=user,
                        title="Курс завершено! 🎓",
                        message=f"Вітаємо! Ви повністю пройшли курс: {lesson.course.title}",
                        notification_type='achievement',
                        link=reverse("courses:course-detail", kwargs={"pk": lesson.course.id})
                    )
                    
                    messages.success(
                        request, f"Вітаємо! Ви отримали значок: {course_badge.name}!"
                    )

        from django.urls import reverse
        from users.models import Notification
        Notification.objects.create(
            user=user,
            title="Урок завершено! ✅",
            message=f"Ви пройшли урок: {lesson.title} з оцінкою {score}%",
            notification_type='success',
            link=reverse("courses:lesson-detail", kwargs={"pk": lesson.id})
        )
        
        messages.success(request, f"Урок завершено! Ваша оцінка: {score}%")

    return redirect("courses:course-detail", pk=lesson.course.id)


@login_required
def course_test_start_view(request, pk):
    course = get_object_or_404(Course, pk=pk)

    if not hasattr(course, "final_test"):
        messages.warning(request, "Для цього курсу ще немає фінального тесту")
        return redirect("courses:course-detail", pk=pk)

    test = course.final_test

    completed_lessons = UserLessonProgress.objects.filter(
        user=request.user, lesson__course=course, is_completed=True
    ).count()
    total_lessons = course.lessons.count()

    if completed_lessons < total_lessons:
        messages.warning(request, "Щоб пройти тест, потрібно завершити всі уроки курсу")
        return redirect("courses:course-detail", pk=pk)

    context = {
        "course": course,
        "test": test,
    }
    return render(request, "courses/test_start.html", context)


@login_required
def course_test_take_view(request, pk):
    course = get_object_or_404(Course, pk=pk)
    test = course.final_test
    questions = test.questions.all().order_by("order")

    if request.method == "POST":
        score = 0
        total_points = 0
        results = []

        for question in questions:
            user_answer = request.POST.get(f"question_{question.id}")
            is_correct = False

            if user_answer:
                correct = question.correct_answer.strip().lower()
                user = user_answer.strip().lower()

                if question.exercise_type == "multiple_choice":
                    is_correct = correct == user
                elif question.exercise_type == "fill_blank":
                    is_correct = correct in user or user in correct
                else:
                    is_correct = correct == user

            points = question.points
            total_points += points
            earned = points if is_correct else 0
            score += earned

            results.append(
                {
                    "question": question,
                    "user_answer": user_answer,
                    "is_correct": is_correct,
                    "correct_answer": question.correct_answer,
                }
            )

        percentage = int((score / total_points) * 100) if total_points > 0 else 0
        passed = percentage >= test.passing_score

        progress, _ = UserCourseProgress.objects.get_or_create(
            user=request.user, course=course
        )

        if percentage > progress.test_score:
            progress.test_score = percentage
            progress.test_passed = passed
            if passed:
                progress.is_completed = True
                progress.completed_at = timezone.now()

                # Check missions
                before_missions = get_missions_status(request.user)

                user_progress, _ = UserProgress.objects.get_or_create(user=request.user)
                leveled_up = user_progress.add_xp(500)

                check_mission_completions(request, before_missions)
                
                from django.urls import reverse
                from users.models import Notification
                Notification.objects.create(
                    user=request.user,
                    title="Іспит складено! 🎓",
                    message=f"Ви успішно склали фінальний іспит курсу '{course.title}'!",
                    notification_type='achievement',
                    link=reverse("courses:course-detail", kwargs={"pk": course.id})
                )

                if leveled_up:
                    messages.info(
                        request, f"Вітаємо! Ви досягли рівня {user_progress.level}!"
                    )

                course_badge = Badge.objects.filter(
                    criteria_type="course_completed", criteria_value=course.id
                ).first()
                if course_badge:
                    UserBadge.objects.get_or_create(
                        user=request.user, badge=course_badge
                    )
                    messages.success(
                        request, f"Вітаємо! Ви отримали значок: {course_badge.name}!"
                    )

            progress.save()

        context = {
            "course": course,
            "test": test,
            "results": results,
            "score": score,
            "total_points": total_points,
            "percentage": percentage,
            "passed": passed,
        }
        return render(request, "courses/test_result.html", context)

    context = {
        "course": course,
        "test": test,
        "questions": questions,
    }
    return render(request, "courses/test_take.html", context)


class CourseListView(APIView):

    def get(self, request):
        language = request.query_params.get("language", None)
        level = request.query_params.get("level", None)

        courses = Course.objects.filter(is_active=True).exclude(language="pl")

        if language:
            courses = courses.filter(language=language)
        if level:
            courses = courses.filter(level=level)

        data = [
            {
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "language": course.get_language_display(),
                "level": course.get_level_display(),
                "lessons_count": course.lessons.count(),
            }
            for course in courses
        ]

        return Response(data)


class CourseDetailView(APIView):

    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk, is_active=True)

        lessons = course.lessons.filter(is_active=True)
        user = request.user if request.user.is_authenticated else None

        lessons_data = []
        for lesson in lessons:
            lesson_data = {
                "id": lesson.id,
                "title": lesson.title,
                "description": lesson.description,
                "order": lesson.order,
                "exercises_count": lesson.exercises.count(),
            }

            if user:
                progress = UserLessonProgress.objects.filter(
                    user=user, lesson=lesson
                ).first()
                if progress:
                    lesson_data["is_completed"] = progress.is_completed
                    lesson_data["score"] = progress.score

            lessons_data.append(lesson_data)

        return Response(
            {
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "language": course.get_language_display(),
                "level": course.get_level_display(),
                "lessons": lessons_data,
            }
        )


class LessonDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        lesson = get_object_or_404(Lesson, pk=pk, is_active=True)
        exercises = lesson.exercises.all()

        exercises_data = []
        for exercise in exercises:
            exercise_data = {
                "id": exercise.id,
                "exercise_type": exercise.get_exercise_type_display(),
                "question": exercise.question,
                "points": exercise.points,
                "order": exercise.order,
            }

            if exercise.options:
                exercise_data["options"] = exercise.options

            exercises_data.append(exercise_data)

        user_progress = UserLessonProgress.objects.filter(
            user=request.user, lesson=lesson
        ).first()

        return Response(
            {
                "id": lesson.id,
                "title": lesson.title,
                "description": lesson.description,
                "content": lesson.content,
                "exercises": exercises_data,
                "progress": (
                    {
                        "is_completed": (
                            user_progress.is_completed if user_progress else False
                        ),
                        "score": user_progress.score if user_progress else 0,
                    }
                    if user_progress
                    else None
                ),
            }
        )


class SubmitExerciseView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        exercise = get_object_or_404(Exercise, pk=pk)
        user_answer = request.data.get("answer", "").strip()

        if not user_answer:
            return Response(
                {"error": "Відповідь не може бути порожньою"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Для вправ курсів використовуємо ручне порівняння
        is_correct = self._check_answer(exercise, user_answer)

        points_earned = exercise.points if is_correct else 0

        attempt = UserExerciseAttempt.objects.create(
            user=request.user,
            exercise=exercise,
            user_answer=user_answer,
            is_correct=is_correct,
            ai_feedback=None,  # Фідбек прибрано
            points_earned=points_earned,
        )

        user_progress, _ = UserProgress.objects.get_or_create(user=request.user)
        if is_correct:
            # Check missions BEFORE state change
            before_missions = get_missions_status(request.user)

            # Перевіряємо, чи це перша правильна спроба взагалі
            already_correct_count = UserExerciseAttempt.objects.filter(
                user=request.user, exercise=exercise, is_correct=True
            ).count()

            if already_correct_count <= 1:  # Оскільки ми вже створили поточну спробу
                user_progress.total_exercises_completed += 1
                user_progress.add_xp(points_earned)

            # Check missions AFTER state change
            check_mission_completions(request, before_missions)

        return Response(
            {
                "is_correct": is_correct,
                "points_earned": points_earned,
                "correct_answer": exercise.correct_answer if not is_correct else None,
            }
        )

    def _check_answer(self, exercise, user_answer):
        correct = exercise.correct_answer.strip().lower()
        user = user_answer.strip().lower()

        if exercise.exercise_type == "multiple_choice":
            return correct == user
        elif exercise.exercise_type == "fill_blank":
            return correct == user or correct in user
        else:
            return correct == user


class CompleteLessonView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        lesson = get_object_or_404(Lesson, pk=pk)
        user = request.user

        exercises = lesson.exercises.all()
        attempts = UserExerciseAttempt.objects.filter(user=user, exercise__in=exercises)

        if not attempts.exists():
            return Response(
                {"error": "Спочатку виконайте хоча б одну вправу"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        total_points = sum(ex.points for ex in exercises)

        earned_points = 0
        for exercise in exercises:
            best_attempt = (
                UserExerciseAttempt.objects.filter(user=user, exercise=exercise)
                .order_by("-points_earned", "-attempted_at")
                .first()
            )

            if best_attempt:
                earned_points += best_attempt.points_earned

        score = int((earned_points / total_points) * 100) if total_points > 0 else 0

        progress, created = UserLessonProgress.objects.get_or_create(
            user=user, lesson=lesson
        )

        if not progress.is_completed:
            progress.is_completed = True
            progress.score = score
            progress.completed_at = timezone.now()
            progress.save()

            user_progress, _ = UserProgress.objects.get_or_create(user=user)
            user_progress.total_lessons_completed += 1
            user_progress.total_xp += earned_points
            user_progress.save()

            total_lessons = lesson.course.lessons.filter(is_active=True).count()
            completed_lessons = UserLessonProgress.objects.filter(
                user=user, lesson__course=lesson.course, is_completed=True
            ).count()

            if completed_lessons >= total_lessons:
                course_progress, _ = UserCourseProgress.objects.get_or_create(
                    user=user, course=lesson.course
                )
                if not course_progress.is_completed:
                    course_progress.is_completed = True
                    course_progress.completed_at = timezone.now()
                    course_progress.save()

                    # Нарахування XP за завершення курсу
                    user_progress.add_xp(300)

                    # Перевіряємо та нараховуємо значок за завершення курсу
                    user_progress.award_badge(
                        "course_completed", criteria_value=lesson.course.id
                    )

        return Response(
            {
                "message": "Урок завершено!",
                "score": score,
                "points_earned": earned_points,
            }
        )
