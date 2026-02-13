from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from .models import Course, Lesson, Exercise, UserLessonProgress, UserExerciseAttempt, CourseTest, UserCourseProgress
from users.models import UserProgress, Badge, UserBadge
from ai_services.services import AIExerciseService
from .forms import FilterForm, ExerciseAnswerForm, MultipleChoiceForm


# Template views
def courses_list_view(request):
    """Список курсів - template view"""
    form = FilterForm(request.GET)
    courses = Course.objects.filter(is_active=True).exclude(language='pl').order_by('language')
    
    if form.is_valid():
        language = form.cleaned_data.get('language')
        level = form.cleaned_data.get('level')
        
        if language:
            courses = courses.filter(language=language)
        if level:
            courses = courses.filter(level=level)
    
    context = {
        'courses': courses,
        'form': form,
    }
    return render(request, 'courses/list.html', context)


def course_detail_view(request, pk):
    """Деталі курсу - template view"""
    course = get_object_or_404(Course, pk=pk, is_active=True)
    lessons = course.lessons.filter(is_active=True).order_by('order')
    
    # Отримуємо прогрес користувача по уроках
    user_progress = {}
    if request.user.is_authenticated:
        progress_list = UserLessonProgress.objects.filter(
            user=request.user,
            lesson__in=lessons
        )
        for progress in progress_list:
            user_progress[progress.lesson.id] = progress
    
    user_course_progress = None
    if request.user.is_authenticated:
        user_course_progress = UserCourseProgress.objects.filter(
            user=request.user,
            course=course
        ).first()

    context = {
        'course': course,
        'lessons': lessons,
        'user_progress': user_progress,
        'user_course_progress': user_course_progress,
        'has_test': hasattr(course, 'final_test'),
    }
    return render(request, 'courses/detail.html', context)


@login_required
def lesson_detail_view(request, pk):
    """Деталі уроку - template view"""
    lesson = get_object_or_404(Lesson, pk=pk, is_active=True)
    exercises = lesson.exercises.all().order_by('order')
    
    # Отримуємо прогрес користувача
    user_progress = UserLessonProgress.objects.filter(
        user=request.user,
        lesson=lesson
    ).first()
    
    # Отримуємо спроби користувача по вправах
    attempts = {}
    if request.user.is_authenticated:
        for exercise in exercises:
            attempt = UserExerciseAttempt.objects.filter(
                user=request.user,
                exercise=exercise
            ).order_by('-attempted_at').first()
            if attempt:
                attempts[exercise.id] = attempt
    
    context = {
        'lesson': lesson,
        'exercises': exercises,
        'user_progress': user_progress,
        'attempts': attempts,
    }
    return render(request, 'courses/lesson.html', context)


@login_required
def submit_exercise_view(request, pk):
    """Відправка відповіді на вправу"""
    exercise = get_object_or_404(Exercise, pk=pk)
    
    if exercise.exercise_type == 'multiple_choice' and exercise.options:
        form = MultipleChoiceForm(request.POST, options=exercise.options)
    else:
        form = ExerciseAnswerForm(request.POST)
    
    if form.is_valid():
        user_answer = form.cleaned_data['answer']
        
        correct = exercise.correct_answer.strip().lower()
        user = user_answer.lower()
        
        if exercise.exercise_type == 'multiple_choice':
            is_correct = correct == user
        elif exercise.exercise_type == 'fill_blank':
            is_correct = correct in user or user in correct
        else:
            is_correct = correct == user
        
        points_earned = exercise.points if is_correct else 0
        
        ai_feedback = None
        if exercise.is_ai_generated or exercise.exercise_type in ['speaking', 'translation']:
            ai_service = AIExerciseService()
            ai_feedback = ai_service.get_feedback(
                exercise.question,
                exercise.correct_answer,
                user_answer,
                exercise.exercise_type
            )
        
        UserExerciseAttempt.objects.create(
            user=request.user,
            exercise=exercise,
            user_answer=user_answer,
            is_correct=is_correct,
            ai_feedback=ai_feedback,
            points_earned=points_earned,
        )
        
        user_progress, _ = UserProgress.objects.get_or_create(user=request.user)
        
        if is_correct:
            # Перевіряємо, чи ця вправа вже була виконана правильно раніше
            already_correct = UserExerciseAttempt.objects.filter(
                user=request.user,
                exercise=exercise,
                is_correct=True
            ).exists()
            
            if not already_correct:
                leveled_up = user_progress.add_xp(points_earned)
                user_progress.total_exercises_completed += 1
                user_progress.save()
                
                if leveled_up:
                    messages.info(request, f'Вітаємо! Ви досягли рівня {user_progress.level}!')
                messages.success(request, f'Правильно! Ви отримали {points_earned} балів.')
            else:
                messages.success(request, 'Правильно! (Ви вже виконували цю вправу раніше)')
        else:
            messages.error(request, 'Неправильно. Спробуйте ще раз!')
        
        if ai_feedback:
            messages.info(request, f'Відгук AI: {ai_feedback}')
        
        return redirect('courses:lesson-detail', pk=exercise.lesson.id)
    
    messages.error(request, 'Помилка при відправці відповіді')
    return redirect('courses:lesson-detail', pk=exercise.lesson.id)


@login_required
def complete_lesson_view(request, pk):
    """Завершення уроку"""
    lesson = get_object_or_404(Lesson, pk=pk)
    user = request.user
    
    exercises = lesson.exercises.all()
    attempts = UserExerciseAttempt.objects.filter(
        user=user,
        exercise__in=exercises
    )
    
    if not attempts.exists():
        messages.warning(request, 'Спочатку виконайте хоча б одну вправу')
        return redirect('courses:lesson-detail', pk=pk)
    
    total_points = sum(ex.points for ex in exercises)
    
    # Рахуємо бали тільки за найкращі спроби по кожній вправі
    earned_points = 0
    for exercise in exercises:
        # Для кожної вправи беремо максимальний зароблений бал серед усіх спроб
        best_attempt = UserExerciseAttempt.objects.filter(
            user=user,
            exercise=exercise
        ).order_by('-points_earned', '-attempted_at').first()
        
        if best_attempt:
            earned_points += best_attempt.points_earned
            
    score = int((earned_points / total_points) * 100) if total_points > 0 else 0
    
    progress, created = UserLessonProgress.objects.get_or_create(
        user=user,
        lesson=lesson
    )
    
    if not progress.is_completed:
        progress.is_completed = True
        progress.score = score
        progress.completed_at = timezone.now()
        progress.save()
        
        user_progress, _ = UserProgress.objects.get_or_create(user=user)
        leveled_up = user_progress.add_xp(earned_points)
        user_progress.total_lessons_completed += 1
        user_progress.save()
        
        if leveled_up:
            messages.info(request, f'Вітаємо! Ви досягли рівня {user_progress.level}!')
        
        messages.success(request, f'Урок завершено! Ваша оцінка: {score}%')
    
    return redirect('courses:course-detail', pk=lesson.course.id)


@login_required
def course_test_start_view(request, pk):
    """Сторінка початку тесту"""
    course = get_object_or_404(Course, pk=pk)
    
    # Перевіряємо чи є тест
    if not hasattr(course, 'final_test'):
        messages.warning(request, 'Для цього курсу ще немає фінального тесту')
        return redirect('courses:course-detail', pk=pk)
        
    test = course.final_test
    
    # Перевіряємо чи пройдені всі уроки
    completed_lessons = UserLessonProgress.objects.filter(
        user=request.user, 
        lesson__course=course, 
        is_completed=True
    ).count()
    total_lessons = course.lessons.count()
    
    if completed_lessons < total_lessons:
        messages.warning(request, 'Щоб пройти тест, потрібно завершити всі уроки курсу')
        return redirect('courses:course-detail', pk=pk)
        
    context = {
        'course': course,
        'test': test,
    }
    return render(request, 'courses/test_start.html', context)


@login_required
def course_test_take_view(request, pk):
    """Проходження тесту"""
    course = get_object_or_404(Course, pk=pk)
    test = course.final_test
    questions = test.questions.all().order_by('order')
    
    if request.method == 'POST':
        score = 0
        total_points = 0
        results = []
        
        for question in questions:
            user_answer = request.POST.get(f'question_{question.id}')
            is_correct = False
            
            if user_answer:
                correct = question.correct_answer.strip().lower()
                user = user_answer.strip().lower()
                
                if question.exercise_type == 'multiple_choice':
                    is_correct = correct == user
                elif question.exercise_type == 'fill_blank':
                    is_correct = correct in user or user in correct
                else:
                    is_correct = correct == user
            
            points = question.points
            total_points += points
            earned = points if is_correct else 0
            score += earned
            
            results.append({
                'question': question,
                'user_answer': user_answer,
                'is_correct': is_correct,
                'correct_answer': question.correct_answer
            })
            
        # Розрахунок результату
        percentage = int((score / total_points) * 100) if total_points > 0 else 0
        passed = percentage >= test.passing_score
        
        # Збереження прогресу
        progress, _ = UserCourseProgress.objects.get_or_create(
            user=request.user,
            course=course
        )
        
        # Оновлюємо якщо кращий результат
        if percentage > progress.test_score:
            progress.test_score = percentage
            progress.test_passed = passed
            if passed:
                progress.is_completed = True
                progress.completed_at = timezone.now()
                
                # Нарахування XP за курс
                user_progress, _ = UserProgress.objects.get_or_create(user=request.user)
                leveled_up = user_progress.add_xp(500) # Бонус за завершення курсу
                if leveled_up:
                    messages.info(request, f'Вітаємо! Ви досягли рівня {user_progress.level}!')
                
                # Перевіряємо та нараховуємо значок за завершення курсу
                course_badge = Badge.objects.filter(
                    criteria_type='course_completed',
                    criteria_value=course.id
                ).first()
                if course_badge:
                    UserBadge.objects.get_or_create(user=request.user, badge=course_badge)
                    messages.success(request, f'Вітаємо! Ви отримали значок: {course_badge.name}!')
                
            progress.save()
            
        context = {
            'course': course,
            'test': test,
            'results': results,
            'score': score,
            'total_points': total_points,
            'percentage': percentage,
            'passed': passed,
        }
        return render(request, 'courses/test_result.html', context)
        
    context = {
        'course': course,
        'test': test,
        'questions': questions,
    }
    return render(request, 'courses/test_take.html', context)

class CourseListView(APIView):
    """Список курсів"""
    
    def get(self, request):
        language = request.query_params.get('language', None)
        level = request.query_params.get('level', None)
        
        courses = Course.objects.filter(is_active=True).exclude(language='pl')
        
        if language:
            courses = courses.filter(language=language)
        if level:
            courses = courses.filter(level=level)
        
        data = [{
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'language': course.get_language_display(),
            'level': course.get_level_display(),
            'lessons_count': course.lessons.count(),
        } for course in courses]
        
        return Response(data)


class CourseDetailView(APIView):
    """Деталі курсу"""
    
    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk, is_active=True)
        
        lessons = course.lessons.filter(is_active=True)
        user = request.user if request.user.is_authenticated else None
        
        lessons_data = []
        for lesson in lessons:
            lesson_data = {
                'id': lesson.id,
                'title': lesson.title,
                'description': lesson.description,
                'order': lesson.order,
                'exercises_count': lesson.exercises.count(),
            }
            
            if user:
                progress = UserLessonProgress.objects.filter(user=user, lesson=lesson).first()
                if progress:
                    lesson_data['is_completed'] = progress.is_completed
                    lesson_data['score'] = progress.score
            
            lessons_data.append(lesson_data)
        
        return Response({
            'id': course.id,
            'title': course.title,
            'description': course.description,
            'language': course.get_language_display(),
            'level': course.get_level_display(),
            'lessons': lessons_data,
        })


class LessonDetailView(APIView):
    """Деталі уроку з вправами"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        lesson = get_object_or_404(Lesson, pk=pk, is_active=True)
        exercises = lesson.exercises.all()
        
        exercises_data = []
        for exercise in exercises:
            exercise_data = {
                'id': exercise.id,
                'exercise_type': exercise.get_exercise_type_display(),
                'question': exercise.question,
                'points': exercise.points,
                'order': exercise.order,
            }
            
            # Не показуємо правильну відповідь та варіанти до спроби
            if exercise.options:
                exercise_data['options'] = exercise.options
            
            exercises_data.append(exercise_data)
        
        user_progress = UserLessonProgress.objects.filter(
            user=request.user,
            lesson=lesson
        ).first()
        
        return Response({
            'id': lesson.id,
            'title': lesson.title,
            'description': lesson.description,
            'content': lesson.content,
            'exercises': exercises_data,
            'progress': {
                'is_completed': user_progress.is_completed if user_progress else False,
                'score': user_progress.score if user_progress else 0,
            } if user_progress else None,
        })


class SubmitExerciseView(APIView):
    """Відправка відповіді на вправу"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        exercise = get_object_or_404(Exercise, pk=pk)
        user_answer = request.data.get('answer', '').strip()
        
        if not user_answer:
            return Response(
                {'error': 'Відповідь не може бути порожньою'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        is_correct = self._check_answer(exercise, user_answer)
        points_earned = exercise.points if is_correct else 0
        
        ai_feedback = None
        if exercise.is_ai_generated or exercise.exercise_type in ['speaking', 'translation']:
            ai_service = AIExerciseService()
            ai_feedback = ai_service.get_feedback(
                exercise.question,
                exercise.correct_answer,
                user_answer,
                exercise.exercise_type
            )
        
        attempt = UserExerciseAttempt.objects.create(
            user=request.user,
            exercise=exercise,
            user_answer=user_answer,
            is_correct=is_correct,
            ai_feedback=ai_feedback,
            points_earned=points_earned,
        )
        
        user_progress, _ = UserProgress.objects.get_or_create(user=request.user)
        if is_correct:
            # Перевіряємо, чи ця вправа вже була виконана правильно раніше
            already_correct = UserExerciseAttempt.objects.filter(
                user=request.user,
                exercise=exercise,
                is_correct=True
            ).exists()
            
            if not already_correct:
                user_progress.total_exercises_completed += 1
                user_progress.total_xp += points_earned
                user_progress.update_activity()
                user_progress.save()
        
        return Response({
            'is_correct': is_correct,
            'points_earned': points_earned,
            'ai_feedback': ai_feedback,
            'correct_answer': exercise.correct_answer if not is_correct else None,
        })
    
    def _check_answer(self, exercise, user_answer):
        """Перевірка відповіді"""
        correct = exercise.correct_answer.strip().lower()
        user = user_answer.lower()
        
        if exercise.exercise_type == 'multiple_choice':
            return correct == user
        elif exercise.exercise_type == 'fill_blank':
            return correct in user or user in correct
        else:
            return correct == user


class CompleteLessonView(APIView):
    """Завершення уроку"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        lesson = get_object_or_404(Lesson, pk=pk)
        user = request.user
        
        exercises = lesson.exercises.all()
        attempts = UserExerciseAttempt.objects.filter(
            user=user,
            exercise__in=exercises
        )
        
        if not attempts.exists():
            return Response(
                {'error': 'Спочатку виконайте хоча б одну вправу'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        total_points = sum(ex.points for ex in exercises)
        
        # Рахуємо бали тільки за найкращі спроби по кожній вправі
        earned_points = 0
        for exercise in exercises:
            best_attempt = UserExerciseAttempt.objects.filter(
                user=user,
                exercise=exercise
            ).order_by('-points_earned', '-attempted_at').first()
            
            if best_attempt:
                earned_points += best_attempt.points_earned
                
        score = int((earned_points / total_points) * 100) if total_points > 0 else 0
        
        progress, created = UserLessonProgress.objects.get_or_create(
            user=user,
            lesson=lesson
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
        
        return Response({
            'message': 'Урок завершено!',
            'score': score,
            'points_earned': earned_points,
        })
