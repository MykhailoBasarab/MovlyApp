from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class TestType(models.Model):
    """Тип тесту (IELTS, TOEFL, тощо)"""
    name = models.CharField(max_length=100, verbose_name='Назва')
    code = models.CharField(max_length=20, unique=True, verbose_name='Код')
    description = models.TextField(verbose_name='Опис')
    duration_minutes = models.IntegerField(validators=[MinValueValidator(1)], verbose_name='Тривалість (хвилин)')
    total_score = models.IntegerField(default=100, verbose_name='Максимальний бал')

    class Meta:
        verbose_name = 'Тип тесту'
        verbose_name_plural = 'Типи тестів'
        db_table = 'test_types'

    def __str__(self):
        return self.name


class Test(models.Model):
    """Тест типу IELTS"""
    test_type = models.ForeignKey(
        TestType,
        on_delete=models.CASCADE,
        related_name='tests',
        verbose_name='Тип тесту'
    )
    language = models.CharField(
        max_length=10,
        choices=[
            ('en', 'English'),
            ('de', 'Deutsch'),
            ('fr', 'Français'),
            ('es', 'Español'),
            ('it', 'Italiano'),
            ('pl', 'Polski'),
        ],
        verbose_name='Мова тесту'
    )
    level = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Початковий'),
            ('elementary', 'Елементарний'),
            ('intermediate', 'Середній'),
            ('upper_intermediate', 'Вище середнього'),
            ('advanced', 'Просунутий'),
        ],
        verbose_name='Рівень'
    )
    title = models.CharField(max_length=200, verbose_name='Назва')
    description = models.TextField(verbose_name='Опис')
    is_active = models.BooleanField(default=True, verbose_name='Активний')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тести'
        db_table = 'tests'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.test_type.name} - {self.title}'


class TestSection(models.Model):
    """Секція тесту (Listening, Reading, Writing, Speaking)"""
    SECTION_TYPES = [
        ('listening', 'Аудіювання'),
        ('reading', 'Читання'),
        ('writing', 'Письмо'),
        ('speaking', 'Говоріння'),
    ]

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name='Тест'
    )
    section_type = models.CharField(
        max_length=20,
        choices=SECTION_TYPES,
        verbose_name='Тип секції'
    )
    title = models.CharField(max_length=200, verbose_name='Назва')
    description = models.TextField(verbose_name='Опис')
    duration_minutes = models.IntegerField(validators=[MinValueValidator(1)], verbose_name='Тривалість (хвилин)')
    max_score = models.IntegerField(default=25, verbose_name='Максимальний бал')
    order = models.IntegerField(validators=[MinValueValidator(1)], verbose_name='Порядок')

    class Meta:
        verbose_name = 'Секція тесту'
        verbose_name_plural = 'Секції тестів'
        db_table = 'test_sections'
        ordering = ['order']

    def __str__(self):
        return f'{self.test.title} - {self.get_section_type_display()}'


class TestQuestion(models.Model):
    """Питання в тесті"""
    QUESTION_TYPES = [
        ('multiple_choice', 'Вибір відповіді'),
        ('fill_blank', 'Заповнити пропуск'),
        ('true_false', 'Правда/Неправда'),
        ('matching', 'Зіставлення'),
        ('short_answer', 'Коротка відповідь'),
        ('essay', 'Есе'),
        ('listening_audio', 'Аудіювання з аудіо'),
        ('speaking_record', 'Говоріння з записом'),
    ]

    section = models.ForeignKey(
        TestSection,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Секція'
    )
    question_type = models.CharField(
        max_length=20,
        choices=QUESTION_TYPES,
        verbose_name='Тип питання'
    )
    question_text = models.TextField(verbose_name='Текст питання')
    audio_url = models.URLField(null=True, blank=True, verbose_name='URL аудіо')
    audio_text = models.TextField(null=True, blank=True, verbose_name='Текст для аудіо (генерація через AI)')
    correct_answer = models.TextField(verbose_name='Правильна відповідь')
    options = models.JSONField(null=True, blank=True, verbose_name='Варіанти відповідей')
    points = models.IntegerField(default=1, validators=[MinValueValidator(1)], verbose_name='Бали')
    order = models.IntegerField(validators=[MinValueValidator(1)], verbose_name='Порядок')
    is_ai_generated = models.BooleanField(default=False, verbose_name='Згенеровано AI')
    ai_prompt = models.TextField(null=True, blank=True, verbose_name='Промпт для AI')

    class Meta:
        verbose_name = 'Питання тесту'
        verbose_name_plural = 'Питання тестів'
        db_table = 'test_questions'
        ordering = ['order']

    def __str__(self):
        return f'{self.section.title} - Питання {self.order}'


class TestAttempt(models.Model):
    """Спроба проходження тесту користувачем"""
    STATUS_CHOICES = [
        ('in_progress', 'В процесі'),
        ('completed', 'Завершено'),
        ('abandoned', 'Перервано'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='test_attempts',
        verbose_name='Користувач'
    )
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='Тест'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='in_progress',
        verbose_name='Статус'
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='Почато о')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='Завершено о')
    total_score = models.IntegerField(default=0, verbose_name='Загальний бал')
    max_score = models.IntegerField(default=100, verbose_name='Максимальний бал')
    listening_score = models.IntegerField(default=0, verbose_name='Бал за аудіювання')
    reading_score = models.IntegerField(default=0, verbose_name='Бал за читання')
    writing_score = models.IntegerField(default=0, verbose_name='Бал за письмо')
    speaking_score = models.IntegerField(default=0, verbose_name='Бал за говоріння')

    class Meta:
        verbose_name = 'Спроба тесту'
        verbose_name_plural = 'Спроби тестів'
        db_table = 'test_attempts'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.user.username} - {self.test.title} - {self.get_status_display()}'


class TestAnswer(models.Model):
    """Відповідь користувача на питання тесту"""
    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Спроба тесту'
    )
    question = models.ForeignKey(
        TestQuestion,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Питання'
    )
    user_answer = models.TextField(verbose_name='Відповідь користувача')
    audio_answer_url = models.URLField(null=True, blank=True, verbose_name='URL аудіо відповіді')
    is_correct = models.BooleanField(null=True, blank=True, verbose_name='Правильно')
    points_earned = models.IntegerField(default=0, verbose_name='Отримано балів')
    ai_feedback = models.TextField(null=True, blank=True, verbose_name='Відгук AI')
    answered_at = models.DateTimeField(auto_now_add=True, verbose_name='Відповідано о')

    class Meta:
        verbose_name = 'Відповідь на питання тесту'
        verbose_name_plural = 'Відповіді на питання тестів'
        db_table = 'test_answers'
        unique_together = ['attempt', 'question']
        ordering = ['answered_at']

    def __str__(self):
        return f'{self.attempt.user.username} - {self.question}'

