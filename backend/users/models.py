from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import localdate


class CustomUser(AbstractUser):
    native_language = models.CharField(
        max_length=10,
        choices=[
            ("uk", "Українська"),
            ("en", "English"),
        ],
        default="uk",
        verbose_name="Рідна мова",
    )
    learning_language = models.CharField(
        max_length=10,
        choices=[
            ("en", "English"),
            ("de", "Deutsch"),
            ("fr", "Français"),
            ("es", "Español"),
            ("it", "Italiano"),
        ],
        default="en",
        verbose_name="Мова вивчення",
    )
    level = models.CharField(
        max_length=20,
        choices=[
            ("beginner", "Початковий"),
            ("elementary", "Елементарний"),
            ("intermediate", "Середній"),
            ("upper_intermediate", "Вище середнього"),
            ("advanced", "Просунутий"),
        ],
        default="beginner",
        verbose_name="Рівень",
    )
    avatar = models.ImageField(
        upload_to="avatars/", null=True, blank=True, verbose_name="Аватар"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Користувач"
        verbose_name_plural = "Користувачі"
        db_table = "users"

    def __str__(self):
        return self.username


class UserProgress(models.Model):
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="progress",
        verbose_name="Користувач",
    )
    total_lessons_completed = models.IntegerField(
        default=0, verbose_name="Пройдено уроків"
    )
    total_exercises_completed = models.IntegerField(
        default=0, verbose_name="Виконано вправ"
    )
    current_streak = models.IntegerField(default=0, verbose_name="Поточна серія днів")
    longest_streak = models.IntegerField(default=0, verbose_name="Найдовша серія днів")
    total_xp = models.IntegerField(default=0, verbose_name="Загальний досвід")
    daily_xp = models.IntegerField(default=0, verbose_name="Досвід за сьогодні")
    daily_goal = models.IntegerField(default=50, verbose_name="Щоденна ціль XP")
    last_activity_date = models.DateField(
        null=True, blank=True, verbose_name="Остання активність"
    )

    class Meta:
        verbose_name = "Прогрес користувача"
        verbose_name_plural = "Прогрес користувачів"
        db_table = "user_progress"

    def update_activity(self):
        today = localdate()

        if self.last_activity_date:
            if self.last_activity_date == today:
                pass
            elif self.last_activity_date == today - timedelta(days=1):
                self.current_streak += 1
                self.daily_xp = 0
            else:
                self.current_streak = 1
                self.daily_xp = 0
        else:
            self.current_streak = 1
            self.daily_xp = 0

        self.last_activity_date = today
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        self.save()

    def add_xp(self, amount):
        old_level = self.level
        self.update_activity()
        self.total_xp += amount
        self.daily_xp += amount
        self.save()

        from .models import Badge, UserBadge

        xp_badges = Badge.objects.filter(
            criteria_type="xp_reached", criteria_value__lte=self.total_xp
        )
        for badge in xp_badges:
            UserBadge.objects.get_or_create(user=self.user, badge=badge)

        return self.level > old_level

    def award_badge(self, criteria_type, criteria_value=None):
        from .models import Badge, UserBadge

        query = Q(criteria_type=criteria_type)
        if criteria_value is not None:
            query &= Q(criteria_value=criteria_value)

        badge = Badge.objects.filter(query).first()
        if badge:
            ub, created = UserBadge.objects.get_or_create(user=self.user, badge=badge)
            return created
        return False

    @property
    def level(self):
        return (self.total_xp // 1000) + 1

    @property
    def rank_title(self):
        xp = self.total_xp
        if xp < 1000:
            return "Новачок"
        elif xp < 3000:
            return "Початківець"
        elif xp < 5000:
            return "Дослідник"
        elif xp < 10000:
            return "Знавець"
        elif xp < 20000:
            return "Експерт"
        elif xp < 35000:
            return "Професіонал"
        elif xp < 50000:
            return "Майстер"
        else:
            return "Легенда"

    @property
    def xp_to_next_level(self):
        return 1000 - (self.total_xp % 1000)

    @property
    def level_progress_percentage(self):
        return (self.total_xp % 1000) / 10

    def __str__(self):
        return f"Прогрес {self.user.username}"


class Badge(models.Model):
    name = models.CharField(max_length=100, verbose_name="Назва")
    description = models.TextField(verbose_name="Опис")
    icon = models.CharField(max_length=50, verbose_name="Іконка (FontAwesome class)")
    criteria_type = models.CharField(
        max_length=50,
        choices=[
            ("course_completed", "Завершення курсу"),
            ("test_completed", "Складання тесту"),
            ("xp_reached", "Досягнення XP"),
            ("streak_reached", "Серія днів"),
            ("exercise_count", "Кількість вправ"),
        ],
        verbose_name="Тип критерію",
    )
    criteria_value = models.IntegerField(verbose_name="Значення критерію")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Значок"
        verbose_name_plural = "Значки"
        db_table = "badges"

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="badges"
    )
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Значок користувача"
        verbose_name_plural = "Значки користувачів"
        db_table = "user_badges"
        unique_together = ["user", "badge"]

    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"
