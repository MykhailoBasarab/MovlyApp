from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from .models import TestType, Test, TestSection, TestQuestion, TestAttempt, TestAnswer
from users.models import UserProgress
from users.services import get_missions_status, check_mission_completions
from ai_services.services import AIExerciseService
from .forms import TestFilterForm, TestAnswerForm, MultipleChoiceTestForm


def tests_list_view(request):
    form = TestFilterForm(request.GET)
    tests = Test.objects.filter(is_active=True).order_by('language')
    
    if form.is_valid():
        language = form.cleaned_data.get('language')
        level = form.cleaned_data.get('level')
        
        if language:
            tests = tests.filter(language=language)
        if level:
            tests = tests.filter(level=level)
    
    completed_test_ids = set()
    started_test_ids = set()
    if request.user.is_authenticated:
        completed_test_ids = set(TestAttempt.objects.filter(
            user=request.user, 
            status='completed'
        ).values_list('test_id', flat=True).distinct())
        
        started_test_ids = set(TestAttempt.objects.filter(
            user=request.user,
            status='in_progress'
        ).values_list('test_id', flat=True).distinct())
    
    context = {
        'tests': tests,
        'form': form,
        'completed_test_ids': completed_test_ids,
        'started_test_ids': started_test_ids,
    }
    return render(request, 'tests/list.html', context)


def test_detail_view(request, pk):
    test = get_object_or_404(Test, pk=pk, is_active=True)
    sections = test.sections.all().order_by('order')
    
    active_attempt = None
    completed_attempt = None
    if request.user.is_authenticated:
        active_attempt = TestAttempt.objects.filter(
            user=request.user,
            test=test,
            status='in_progress'
        ).first()
        
        completed_attempt = TestAttempt.objects.filter(
            user=request.user,
            test=test,
            status='completed'
        ).order_by('-completed_at').first()
    
    context = {
        'test': test,
        'sections': sections,
        'active_attempt': active_attempt,
        'completed_attempt': completed_attempt,
    }
    return render(request, 'tests/detail.html', context)


@login_required
def test_attempt_view(request, pk):
    attempt = get_object_or_404(TestAttempt, pk=pk, user=request.user)
    
    if attempt.status not in ['in_progress', 'completed']:
        messages.warning(request, 'Цей тест не доступний для перегляду')
        return redirect('tests:test-detail', pk=attempt.test.id)
    
    sections = list(attempt.test.sections.all().order_by('order'))
    
    global_counter = 1
    for section in sections:
        questions = list(section.questions.all().order_by('order'))
        for question in questions:
            question.global_index = global_counter
            global_counter += 1
        section.questions_list = questions
    
    answers = {}
    answered_count = 0
    total_questions = 0
    for section in sections:
        section_answers = TestAnswer.objects.filter(
            attempt=attempt,
            question__section=section
        )
        section_dict = {}
        for answer in section_answers:
            section_dict[answer.question.id] = answer
            answered_count += 1
        if section_dict:
            answers[section.id] = section_dict
        
        total_questions += len(section.questions_list)
    
    context = {
        'attempt': attempt,
        'test': attempt.test,
        'sections': sections,
        'answers': answers,
        'answered_count': answered_count,
        'total_questions': total_questions,
    }
    return render(request, 'tests/attempt.html', context)


@login_required
def start_test_view(request, pk):
    test = get_object_or_404(Test, pk=pk, is_active=True)
    
    active_attempt = TestAttempt.objects.filter(
        user=request.user,
        test=test,
        status='in_progress'
    ).first()
    
    if active_attempt:
        return redirect('tests:test-attempt', pk=active_attempt.id)
    
    attempt = TestAttempt.objects.create(
        user=request.user,
        test=test,
        status='in_progress',
        max_score=test.test_type.total_score
    )
    
    messages.info(request, 'Тест розпочато! Успіхів!')
    return redirect('tests:test-attempt', pk=attempt.id)


@login_required
def submit_test_answer_view(request, attempt_id, question_id):
    attempt = get_object_or_404(TestAttempt, pk=attempt_id, user=request.user)
    question = get_object_or_404(TestQuestion, pk=question_id, section__test=attempt.test)
    
    if attempt.status != 'in_progress':
        messages.error(request, 'Тест вже завершено')
        return redirect('tests:test-attempt', pk=attempt_id)
    
    if question.question_type == 'multiple_choice' and question.options:
        form = MultipleChoiceTestForm(request.POST, options=question.options)
    else:
        form = TestAnswerForm(request.POST)
    
    if form.is_valid():
        user_answer = form.cleaned_data['answer']
        
        correct = question.correct_answer.strip().lower()
        user = user_answer.strip().lower()
        
        is_correct = False
        if question.question_type in ['essay', 'short_answer']:
            ai_service = AIExerciseService()
            ai_result = ai_service.check_answer_and_get_feedback(
                question.question_text,
                question.correct_answer,
                user_answer,
                question.question_type
            )
            is_correct = ai_result['is_correct']
            ai_feedback = ai_result['feedback']
        else:
            ai_feedback = None
            correct = question.correct_answer.strip().lower()
            user = user_answer.strip().lower()
            
            if question.question_type == 'multiple_choice':
                is_correct = correct == user
            elif question.question_type == 'true_false':
                is_correct = correct == user
            elif question.question_type == 'fill_blank':
                is_correct = correct == user

        points_earned = question.points if is_correct else 0
        
        answer, created = TestAnswer.objects.get_or_create(
            attempt=attempt,
            question=question,
            defaults={
                'user_answer': user_answer,
                'is_correct': is_correct,
                'points_earned': points_earned,
                'ai_feedback': ai_feedback,
            }
        )
        
        if not created:
            answer.user_answer = user_answer
            answer.is_correct = is_correct
            answer.points_earned = points_earned
            answer.ai_feedback = ai_feedback
            answer.save()
        
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'
        
        if not is_ajax:
            if is_correct:
                messages.success(request, f'Правильно! Ви отримали {points_earned} балів.')
            else:
                messages.error(request, f'Неправильно.')
        
        if is_ajax:
            return JsonResponse({
                'success': True,
                'is_correct': is_correct,
                'points_earned': points_earned,
                'user_answer': user_answer,
                'correct_answer': question.correct_answer,
                'ai_feedback': ai_feedback
            })
            
        return redirect('tests:test-attempt', pk=attempt_id)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        return JsonResponse({'success': False, 'error': 'Помилка при відправці відповіді'}, status=400)
        
    messages.error(request, 'Помилка при відправці відповіді')
    return redirect('tests:test-attempt', pk=attempt_id)


@login_required
def complete_test_view(request, pk):
    attempt = get_object_or_404(TestAttempt, pk=pk, user=request.user)
    
    if attempt.status != 'in_progress':
        messages.warning(request, 'Тест вже завершено')
        return redirect('tests:test-detail', pk=attempt.test.id)
    
    sections = attempt.test.sections.all()
    reading_score = 0
    writing_score = 0
    
    for section in sections:
        answers = TestAnswer.objects.filter(
            attempt=attempt,
            question__section=section
        )
        section_score = sum(a.points_earned for a in answers)
        if section.section_type == 'reading':
            reading_score += section_score
        elif section.section_type == 'writing':
            writing_score += section_score
        else:
            reading_score += section_score
            
    total_score = reading_score + writing_score
    
    attempt.status = 'completed'
    attempt.completed_at = timezone.now()
    attempt.total_score = total_score
    attempt.reading_score = reading_score
    attempt.writing_score = writing_score
    attempt.save()
    
    attempt.save()
    
    user_progress, _ = UserProgress.objects.get_or_create(user=request.user)
    
    # Check missions BEFORE adding XP
    before_missions = get_missions_status(request.user)
    
    xp_reward = int(total_score * 0.5) + 50
    user_progress.add_xp(xp_reward)
    
    # Check missions AFTER adding XP
    check_mission_completions(request, before_missions)
    
    user_progress.award_badge('test_completed', criteria_value=attempt.test.id)
    
    messages.success(request, f'Тест завершено! Ваш результат: {total_score}/{attempt.max_score} балів')
    return redirect('tests:test-detail', pk=attempt.test.id)


class TestTypeListView(APIView):
    def get(self, request):
        test_types = TestType.objects.all()
        data = [{
            'id': tt.id,
            'name': tt.name,
            'code': tt.code,
            'description': tt.description,
            'duration_minutes': tt.duration_minutes,
            'total_score': tt.total_score,
        } for tt in test_types]
        return Response(data)


class TestListView(APIView):
    def get(self, request):
        language = request.query_params.get('language', None)
        level = request.query_params.get('level', None)
        test_type = request.query_params.get('test_type', None)
        
        tests = Test.objects.filter(is_active=True)
        
        if language:
            tests = tests.filter(language=language)
        if level:
            tests = tests.filter(level=level)
        if test_type:
            tests = tests.filter(test_type__code=test_type)
        
        data = [{
            'id': test.id,
            'title': test.title,
            'description': test.description,
            'test_type': test.test_type.name,
            'language': test.get_language_display(),
            'level': test.get_level_display(),
            'sections_count': test.sections.count(),
        } for test in tests]
        
        return Response(data)


class TestDetailView(APIView):
    def get(self, request, pk):
        test = get_object_or_404(Test, pk=pk, is_active=True)
        
        sections = test.sections.all()
        sections_data = [{
            'id': section.id,
            'title': section.title,
            'section_type': section.get_section_type_display(),
            'duration_minutes': section.duration_minutes,
            'max_score': section.max_score,
            'questions_count': section.questions.count(),
        } for section in sections]
        
        return Response({
            'id': test.id,
            'title': test.title,
            'description': test.description,
            'test_type': test.test_type.name,
            'language': test.get_language_display(),
            'level': test.get_level_display(),
            'sections': sections_data,
        })


class StartTestView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        test = get_object_or_404(Test, pk=pk, is_active=True)
        
        active_attempt = TestAttempt.objects.filter(
            user=request.user,
            test=test,
            status='in_progress'
        ).first()
        
        if active_attempt:
            return Response({
                'attempt_id': active_attempt.id,
                'message': 'У вас вже є активна спроба цього тесту'
            })
        
        attempt = TestAttempt.objects.create(
            user=request.user,
            test=test,
            status='in_progress',
            max_score=test.test_type.total_score
        )
        
        return Response({
            'attempt_id': attempt.id,
            'test_id': test.id,
            'started_at': attempt.started_at,
            'message': 'Тест розпочато'
        }, status=status.HTTP_201_CREATED)


class TestAttemptDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        attempt = get_object_or_404(TestAttempt, pk=pk, user=request.user)
        
        sections = attempt.test.sections.all()
        sections_data = []
        for section in sections:
            answered_count = TestAnswer.objects.filter(
                attempt=attempt,
                question__section=section
            ).count()
            
            sections_data.append({
                'id': section.id,
                'title': section.title,
                'section_type': section.get_section_type_display(),
                'duration_minutes': section.duration_minutes,
                'questions_count': section.questions.count(),
                'answered_count': answered_count,
            })
        
        return Response({
            'id': attempt.id,
            'test': {
                'id': attempt.test.id,
                'title': attempt.test.title,
            },
            'status': attempt.get_status_display(),
            'started_at': attempt.started_at,
            'completed_at': attempt.completed_at,
            'sections': sections_data,
            'scores': {
                'total': attempt.total_score,
                'max': attempt.max_score,
                'reading': attempt.reading_score,
                'writing': attempt.writing_score,
            } if attempt.status == 'completed' else None,
        })


class SectionQuestionsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk, section_id):
        attempt = get_object_or_404(TestAttempt, pk=pk, user=request.user)
        section = get_object_or_404(TestSection, pk=section_id, test=attempt.test)
        
        questions = section.questions.all()
        questions_data = []
        
        for question in questions:
            answer = TestAnswer.objects.filter(
                attempt=attempt,
                question=question
            ).first()
            
            question_data = {
                'id': question.id,
                'question_type': question.get_question_type_display(),
                'question_text': question.question_text,
                'points': question.points,
                'order': question.order,
            }
            
            
            if question.options:
                question_data['options'] = question.options
            
            if answer:
                question_data['user_answer'] = answer.user_answer
                question_data['is_correct'] = answer.is_correct
                question_data['points_earned'] = answer.points_earned
            
            questions_data.append(question_data)
        
        return Response({
            'section': {
                'id': section.id,
                'title': section.title,
                'section_type': section.get_section_type_display(),
                'duration_minutes': section.duration_minutes,
            },
            'questions': questions_data,
        })


class SubmitAnswerView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        attempt = get_object_or_404(TestAttempt, pk=pk, user=request.user)
        
        if attempt.status != 'in_progress':
            return Response(
                {'error': 'Тест вже завершено або перервано'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        question_id = request.data.get('question_id')
        user_answer = request.data.get('answer', '').strip()
        
        if not question_id:
            return Response(
                {'error': 'Не вказано ID питання'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        question = get_object_or_404(TestQuestion, pk=question_id, section__test=attempt.test)
        
        if question.question_type in ['essay', 'short_answer']:
            ai_service = AIExerciseService()
            ai_result = ai_service.check_answer_and_get_feedback(
                question.question_text,
                question.correct_answer,
                user_answer,
                question.question_type
            )
            is_correct = ai_result['is_correct']
            ai_feedback = ai_result['feedback']
        else:
            ai_feedback = None
            is_correct = self._check_answer(question, user_answer)
            
        points_earned = question.points if is_correct else 0
        
        answer, created = TestAnswer.objects.get_or_create(
            attempt=attempt,
            question=question,
            defaults={
                'user_answer': user_answer,
                'is_correct': is_correct,
                'points_earned': points_earned,
                'ai_feedback': ai_feedback,
            }
        )
        
        if not created:
            answer.user_answer = user_answer
            answer.is_correct = is_correct
            answer.points_earned = points_earned
            answer.ai_feedback = ai_feedback
            answer.save()
        
        return Response({
            'is_correct': is_correct,
            'points_earned': points_earned,
            'correct_answer': question.correct_answer if not is_correct else None,
            'ai_feedback': ai_feedback
        })
    
    def _check_answer(self, question, user_answer):
        correct = question.correct_answer.strip().lower()
        user = user_answer.lower()
        
        if question.question_type == 'multiple_choice':
            return correct == user
        elif question.question_type == 'true_false':
            return correct == user
        elif question.question_type == 'fill_blank':
            return correct in user or user in correct
        else:
            return False


class CompleteTestView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        attempt = get_object_or_404(TestAttempt, pk=pk, user=request.user)
        
        if attempt.status != 'in_progress':
            return Response(
                {'error': 'Тест вже завершено'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sections = attempt.test.sections.all()
        reading_score = 0
        writing_score = 0
        
        for section in sections:
            answers = TestAnswer.objects.filter(
                attempt=attempt,
                question__section=section
            )
            section_score = sum(a.points_earned for a in answers)
            
            if section.section_type == 'reading':
                reading_score += section_score
            elif section.section_type == 'writing':
                writing_score += section_score
            else:
                reading_score += section_score
        
        total_score = reading_score + writing_score
        
        attempt.status = 'completed'
        attempt.completed_at = timezone.now()
        attempt.total_score = total_score
        attempt.reading_score = reading_score
        attempt.writing_score = writing_score
        attempt.save()
        
        progress_obj, _ = UserProgress.objects.get_or_create(user=request.user)
        xp_reward = int(total_score * 0.5) + 50
        progress_obj.add_xp(xp_reward)
        progress_obj.award_badge('test_completed', criteria_value=attempt.test.id)
        
        return Response({
            'message': 'Тест завершено!',
            'total_score': total_score,
            'max_score': attempt.max_score,
            'scores': {
                'reading': reading_score,
                'writing': writing_score,
            }
        })
