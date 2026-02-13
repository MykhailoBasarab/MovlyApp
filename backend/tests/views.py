from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import TestType, Test, TestSection, TestQuestion, TestAttempt, TestAnswer
from ai_services.services import AIExerciseService, AITextToSpeechService
from .forms import TestFilterForm, TestAnswerForm, MultipleChoiceTestForm


# Template views
def tests_list_view(request):
    """Список тестів - template view"""
    form = TestFilterForm(request.GET)
    tests = Test.objects.filter(is_active=True)
    
    if form.is_valid():
        language = form.cleaned_data.get('language')
        level = form.cleaned_data.get('level')
        
        if language:
            tests = tests.filter(language=language)
        if level:
            tests = tests.filter(level=level)
    
    context = {
        'tests': tests,
        'form': form,
    }
    return render(request, 'tests/list.html', context)


def test_detail_view(request, pk):
    """Деталі тесту - template view"""
    test = get_object_or_404(Test, pk=pk, is_active=True)
    sections = test.sections.all().order_by('order')
    
    # Перевірка чи є активна спроба
    active_attempt = None
    if request.user.is_authenticated:
        active_attempt = TestAttempt.objects.filter(
            user=request.user,
            test=test,
            status='in_progress'
        ).first()
    
    context = {
        'test': test,
        'sections': sections,
        'active_attempt': active_attempt,
    }
    return render(request, 'tests/detail.html', context)


@login_required
def test_attempt_view(request, pk):
    """Проходження тесту - template view"""
    attempt = get_object_or_404(TestAttempt, pk=pk, user=request.user)
    
    if attempt.status != 'in_progress':
        messages.warning(request, 'Цей тест вже завершено')
        return redirect('tests:test-detail', pk=attempt.test.id)
    
    sections = attempt.test.sections.all().order_by('order')
    
    # Отримуємо відповіді користувача
    answers = {}
    for section in sections:
        section_answers = TestAnswer.objects.filter(
            attempt=attempt,
            question__section=section
        )
        section_dict = {}
        for answer in section_answers:
            section_dict[answer.question.id] = answer
        if section_dict:
            answers[section.id] = section_dict
    
    context = {
        'attempt': attempt,
        'test': attempt.test,
        'sections': sections,
        'answers': answers,
    }
    return render(request, 'tests/attempt.html', context)


@login_required
def start_test_view(request, pk):
    """Початок проходження тесту"""
    test = get_object_or_404(Test, pk=pk, is_active=True)
    
    # Перевірка чи є активна спроба
    active_attempt = TestAttempt.objects.filter(
        user=request.user,
        test=test,
        status='in_progress'
    ).first()
    
    if active_attempt:
        return redirect('tests:test-attempt', pk=active_attempt.id)
    
    # Створення нової спроби
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
    """Відправка відповіді на питання тесту"""
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
        
        # Перевірка відповіді
        correct = question.correct_answer.strip().lower()
        user = user_answer.lower()
        
        if question.question_type == 'multiple_choice':
            is_correct = correct == user
        elif question.question_type == 'true_false':
            is_correct = correct == user
        elif question.question_type == 'fill_blank':
            is_correct = correct in user or user in correct
        else:
            is_correct = False
        
        points_earned = question.points if is_correct else 0
        
        # AI відгук для складних типів
        ai_feedback = None
        if question.question_type in ['essay', 'speaking_record', 'short_answer']:
            ai_service = AIExerciseService()
            ai_feedback = ai_service.get_feedback(
                question.question_text,
                question.correct_answer,
                user_answer,
                question.question_type
            )
        
        # Оновлення або створення відповіді
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
        
        if is_correct:
            messages.success(request, f'Правильно! Ви отримали {points_earned} балів.')
        else:
            messages.error(request, f'Неправильно.')
        
        return redirect('tests:test-attempt', pk=attempt_id)
    
    messages.error(request, 'Помилка при відправці відповіді')
    return redirect('tests:test-attempt', pk=attempt_id)


@login_required
def complete_test_view(request, pk):
    """Завершення тесту"""
    attempt = get_object_or_404(TestAttempt, pk=pk, user=request.user)
    
    if attempt.status != 'in_progress':
        messages.warning(request, 'Тест вже завершено')
        return redirect('tests:test-detail', pk=attempt.test.id)
    
    # Підрахунок балів по секціях
    sections = attempt.test.sections.all()
    listening_score = 0
    reading_score = 0
    writing_score = 0
    speaking_score = 0
    
    for section in sections:
        answers = TestAnswer.objects.filter(
            attempt=attempt,
            question__section=section
        )
        section_score = sum(a.points_earned for a in answers)
        
        if section.section_type == 'listening':
            listening_score = section_score
        elif section.section_type == 'reading':
            reading_score = section_score
        elif section.section_type == 'writing':
            writing_score = section_score
        elif section.section_type == 'speaking':
            speaking_score = section_score
    
    total_score = listening_score + reading_score + writing_score + speaking_score
    
    # Оновлення спроби
    attempt.status = 'completed'
    attempt.completed_at = timezone.now()
    attempt.total_score = total_score
    attempt.listening_score = listening_score
    attempt.reading_score = reading_score
    attempt.writing_score = writing_score
    attempt.speaking_score = speaking_score
    attempt.save()
    
    messages.success(request, f'Тест завершено! Ваш результат: {total_score}/{attempt.max_score} балів')
    return redirect('tests:test-detail', pk=attempt.test.id)


# API Views (залишаються як були)
class TestTypeListView(APIView):
    """Список типів тестів"""
    
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
    """Список тестів"""
    
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
    """Деталі тесту"""
    
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
    """Початок проходження тесту"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        test = get_object_or_404(Test, pk=pk, is_active=True)
        
        # Перевірка чи є активна спроба
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
        
        # Створення нової спроби
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
    """Деталі спроби тесту"""
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
                'listening': attempt.listening_score,
                'reading': attempt.reading_score,
                'writing': attempt.writing_score,
                'speaking': attempt.speaking_score,
            } if attempt.status == 'completed' else None,
        })


class SectionQuestionsView(APIView):
    """Питання секції тесту"""
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
            
            # Додаємо аудіо якщо є
            if question.audio_url:
                question_data['audio_url'] = question.audio_url
            elif question.audio_text and question.is_ai_generated:
                question_data['audio_text'] = question.audio_text
                question_data['needs_audio_generation'] = True
            
            # Додаємо варіанти відповідей для multiple choice
            if question.options:
                question_data['options'] = question.options
            
            # Додаємо відповідь користувача якщо є
            if answer:
                question_data['user_answer'] = answer.user_answer
                question_data['is_correct'] = answer.is_correct
                question_data['points_earned'] = answer.points_earned
                if answer.audio_answer_url:
                    question_data['audio_answer_url'] = answer.audio_answer_url
            
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
    """Відправка відповіді на питання тесту"""
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
        audio_answer_url = request.data.get('audio_answer_url', None)
        
        if not question_id:
            return Response(
                {'error': 'Не вказано ID питання'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        question = get_object_or_404(TestQuestion, pk=question_id, section__test=attempt.test)
        
        # Перевірка відповіді
        is_correct = self._check_answer(question, user_answer)
        points_earned = question.points if is_correct else 0
        
        # AI відгук для складних типів питань
        ai_feedback = None
        if question.question_type in ['essay', 'speaking_record', 'short_answer']:
            ai_service = AIExerciseService()
            ai_feedback = ai_service.get_feedback(
                question.question_text,
                question.correct_answer,
                user_answer,
                question.question_type
            )
        
        # Оновлення або створення відповіді
        answer, created = TestAnswer.objects.get_or_create(
            attempt=attempt,
            question=question,
            defaults={
                'user_answer': user_answer,
                'audio_answer_url': audio_answer_url,
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
            if audio_answer_url:
                answer.audio_answer_url = audio_answer_url
            answer.save()
        
        return Response({
            'is_correct': is_correct,
            'points_earned': points_earned,
            'ai_feedback': ai_feedback,
            'correct_answer': question.correct_answer if not is_correct else None,
        })
    
    def _check_answer(self, question, user_answer):
        """Перевірка відповіді"""
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
    """Завершення тесту"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        attempt = get_object_or_404(TestAttempt, pk=pk, user=request.user)
        
        if attempt.status != 'in_progress':
            return Response(
                {'error': 'Тест вже завершено'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Підрахунок балів по секціях
        sections = attempt.test.sections.all()
        listening_score = 0
        reading_score = 0
        writing_score = 0
        speaking_score = 0
        
        for section in sections:
            answers = TestAnswer.objects.filter(
                attempt=attempt,
                question__section=section
            )
            section_score = sum(a.points_earned for a in answers)
            
            if section.section_type == 'listening':
                listening_score = section_score
            elif section.section_type == 'reading':
                reading_score = section_score
            elif section.section_type == 'writing':
                writing_score = section_score
            elif section.section_type == 'speaking':
                speaking_score = section_score
        
        total_score = listening_score + reading_score + writing_score + speaking_score
        
        # Оновлення спроби
        attempt.status = 'completed'
        attempt.completed_at = timezone.now()
        attempt.total_score = total_score
        attempt.listening_score = listening_score
        attempt.reading_score = reading_score
        attempt.writing_score = writing_score
        attempt.speaking_score = speaking_score
        attempt.save()
        
        return Response({
            'message': 'Тест завершено!',
            'total_score': total_score,
            'max_score': attempt.max_score,
            'scores': {
                'listening': listening_score,
                'reading': reading_score,
                'writing': writing_score,
                'speaking': speaking_score,
            }
        })


class GenerateAudioView(APIView):
    """Генерація аудіо через AI"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        attempt = get_object_or_404(TestAttempt, pk=pk, user=request.user)
        question_id = request.data.get('question_id')
        text = request.data.get('text')
        
        if not question_id or not text:
            return Response(
                {'error': 'Не вказано question_id або text'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        question = get_object_or_404(TestQuestion, pk=question_id, section__test=attempt.test)
        
        # Генерація аудіо через AI
        tts_service = AITextToSpeechService()
        audio_url = tts_service.generate_speech(text, question.section.test.language)
        
        if not audio_url:
            return Response(
                {'error': 'Не вдалося згенерувати аудіо'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Оновлення питання з URL аудіо
        if not question.audio_url:
            question.audio_url = audio_url
            question.save()
        
        return Response({
            'audio_url': audio_url,
            'question_id': question.id,
        })
