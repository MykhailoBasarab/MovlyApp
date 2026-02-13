from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Розширена модель користувача"""
    native_language = models.CharField(
        max_length=10,
        choices=[
            ('uk', 'Українська'),
            ('en', 'English'),
        ],
        default='uk',
        verbose_name='Рідна мова'
    )
    learning_language = models.CharField(
        max_length=10,
        choices=[
            ('en', 'English'),
            ('de', 'Deutsch'),
            ('fr', 'Français'),
            ('es', 'Español'),
            ('it', 'Italiano'),
        ],
        default='en',
        verbose_name='Мова вивчення'
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
        default='beginner',
        verbose_name='Рівень'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Аватар'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Користувач'
        verbose_name_plural = 'Користувачі'
        db_table = 'users'

    def __str__(self):
        return self.username


from django.utils import timezone
from datetime import timedelta

class UserProgress(models.Model):
    """Прогрес користувача"""
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='progress',
        verbose_name='Користувач'
    )
    total_lessons_completed = models.IntegerField(default=0, verbose_name='Пройдено уроків')
    total_exercises_completed = models.IntegerField(default=0, verbose_name='Виконано вправ')
    current_streak = models.IntegerField(default=0, verbose_name='Поточна серія днів')
    longest_streak = models.IntegerField(default=0, verbose_name='Найдовша серія днів')
    total_xp = models.IntegerField(default=0, verbose_name='Загальний досвід')
    daily_xp = models.IntegerField(default=0, verbose_name='Досвід за сьогодні')
    daily_goal = models.IntegerField(default=50, verbose_name='Щоденна ціль XP')
    last_activity_date = models.DateField(null=True, blank=True, verbose_name='Остання активність')

    class Meta:
        verbose_name = 'Прогрес користувача'
        verbose_name_plural = 'Прогрес користувачів'
        db_table = 'user_progress'

    def update_activity(self):
        """Оновлення серії днів активності та скидання щоденного досвіду"""
        today = timezone.now().date()
        
        if self.last_activity_date:
            if self.last_activity_date == today:
                # Вже була активність сьогодні
                pass
            elif self.last_activity_date == today - timedelta(days=1):
                # Активність була вчора, продовжуємо серію
                self.current_streak += 1
                self.daily_xp = 0  # Новий день - скидаємо XP
            else:
                # Перерва в навчанні
                self.current_streak = 1
                self.daily_xp = 0
        else:
            # Перша активність
            self.current_streak = 1
            self.daily_xp = 0
            
        self.last_activity_date = today
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        self.save()

    def add_xp(self, amount):
        """Додавання досвіду та повернення True, якщо рівень підвищився"""
        old_level = self.level
        self.update_activity()
        self.total_xp += amount
        self.daily_xp += amount
        self.save()
        return self.level > old_level

    @property
    def level(self):
        """Розрахунок рівня на основі XP (кожні 1000 XP = 1 рівень)"""
        return (self.total_xp // 1000) + 1

    @property
    def xp_to_next_level(self):
        """Скільки XP залишилось до наступного рівня"""
        return 1000 - (self.total_xp % 1000)

    @property
    def level_progress_percentage(self):
        """Відсоток прогресу до наступного рівня"""
        return (self.total_xp % 1000) / 10

    def __str__(self):
        return f'Прогрес {self.user.username}'



class Badge(models.Model):
    """Модель значка/досягнення"""
    name = models.CharField(max_length=100, verbose_name='Назва')
    description = models.TextField(verbose_name='Опис')
    icon = models.CharField(max_length=50, verbose_name='Іконка (FontAwesome class)')
    criteria_type = models.CharField(
        max_length=50,
        choices=[
            ('course_completed', 'Завершення курсу'),
            ('xp_reached', 'Досягнення XP'),
            ('streak_reached', 'Серія днів'),
            ('exercise_count', 'Кількість вправ'),
        ],
        verbose_name='Тип критерію'
    )
    criteria_value = models.IntegerField(verbose_name='Значення критерію')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Значок'
        verbose_name_plural = 'Значки'
        db_table = 'badges'

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    """Значки, отримані користувачем"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Значок користувача'
        verbose_name_plural = 'Значки користувачів'
        db_table = 'user_badges'
        unique_together = ['user', 'badge']

    def __str__(self):
        return f'{self.user.username} - {self.badge.name}'
