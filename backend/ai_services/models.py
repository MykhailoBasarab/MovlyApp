from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class AIInteraction(models.Model):
    """Модель для збереження взаємодій з AI"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_interactions',
        verbose_name='Користувач'
    )
    interaction_type = models.CharField(
        max_length=50,
        choices=[
            ('exercise_generation', 'Генерація вправи'),
            ('feedback', 'Відгук'),
            ('answer_check', 'Перевірка відповіді'),
            ('audio_generation', 'Генерація аудіо'),
        ],
        verbose_name='Тип взаємодії'
    )
    prompt = models.TextField(verbose_name='Запит')
    response = models.TextField(verbose_name='Відповідь AI')
    tokens_used = models.IntegerField(default=0, verbose_name='Використано токенів')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Створено')

    class Meta:
        verbose_name = 'Взаємодія з AI'
        verbose_name_plural = 'Взаємодії з AI'
        db_table = 'ai_interactions'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} - {self.get_interaction_type_display()} - {self.created_at}'


class LearningAnalytics(models.Model):
    """Аналітика навчання (зберігається в окремій БД)"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analytics',
        verbose_name='Користувач'
    )
    date = models.DateField(verbose_name='Дата')
    exercises_completed = models.IntegerField(default=0, verbose_name='Виконано вправ')
    lessons_completed = models.IntegerField(default=0, verbose_name='Завершено уроків')
    time_spent_minutes = models.IntegerField(default=0, verbose_name='Час навчання (хв)')
    accuracy_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name='Точність (%)'
    )
    ai_interactions_count = models.IntegerField(default=0, verbose_name='Взаємодій з AI')

    class Meta:
        verbose_name = 'Аналітика навчання'
        verbose_name_plural = 'Аналітика навчання'
        db_table = 'learning_analytics'
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f'{self.user.username} - {self.date}'

