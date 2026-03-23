from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

User = get_user_model()


class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name="Назва")
    description = models.TextField(verbose_name="Опис")
    language = models.CharField(
        max_length=10,
        choices=[
            ("en", "English"),
            ("de", "Deutsch"),
            ("fr", "Français"),
            ("es", "Español"),
            ("it", "Italiano"),
        ],
        verbose_name="Мова курсу",
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
        verbose_name="Рівень",
    )
    image = models.ImageField(
        upload_to="courses/", null=True, blank=True, verbose_name="Зображення"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активний")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курси"
        db_table = "courses"
        ordering = ["-created_at"]

    def get_flag(self):
        """Повертає емодзі прапора для відповідної мови"""
        flags = {
            "en": "🇬🇧",
            "de": "🇩🇪",
            "fr": "🇫🇷",
            "es": "🇪🇸",
            "it": "🇮🇹",
        }
        return flags.get(self.language, "🌐")

    def get_greeting(self):
        """Повертає привітання на відповідній мові"""
        greetings = {
            "en": "Hello",
            "de": "Hallo",
            "fr": "Bonjour",
            "es": "Hola",
            "it": "Ciao",
        }
        return greetings.get(self.language, "Привіт")

    def get_code(self):
        """Повертає код мови для фонового декору"""
        return self.language.upper()

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """Урок в курсі"""

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="lessons", verbose_name="Курс"
    )
    title = models.CharField(max_length=200, verbose_name="Назва")
    description = models.TextField(verbose_name="Опис")
    order = models.IntegerField(
        validators=[MinValueValidator(1)], verbose_name="Порядок"
    )
    content = models.TextField(verbose_name="Контент уроку")
    is_active = models.BooleanField(default=True, verbose_name="Активний")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        db_table = "lessons"
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class CourseTest(models.Model):
    """Фінальний тест курсу"""

    course = models.OneToOneField(
        Course, on_delete=models.CASCADE, related_name="final_test", verbose_name="Курс"
    )
    title = models.CharField(max_length=200, verbose_name="Назва")
    description = models.TextField(verbose_name="Опис")
    passing_score = models.IntegerField(
        default=80,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Прохідний бал",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Фінальний тест"
        verbose_name_plural = "Фінальні тести"
        db_table = "course_tests"

    def __str__(self):
        return f"Тест: {self.course.title}"


class Exercise(models.Model):
    EXERCISE_TYPES = [
        ("multiple_choice", "Вибір відповіді"),
        ("fill_blank", "Заповнити пропуск"),
        ("translation", "Переклад"),
        ("listening", "Аудіювання"),
        ("speaking", "Говоріння"),
        ("ai_generated", "Згенерована"),
    ]

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="exercises",
        verbose_name="Урок",
        null=True,
        blank=True,
    )
    course_test = models.ForeignKey(
        CourseTest,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Тест курсу",
        null=True,
        blank=True,
    )
    exercise_type = models.CharField(
        max_length=20, choices=EXERCISE_TYPES, verbose_name="Тип вправи"
    )
    question = models.TextField(verbose_name="Питання")
    correct_answer = models.TextField(verbose_name="Правильна відповідь")
    options = models.JSONField(
        null=True, blank=True, verbose_name="Варіанти відповідей"
    )
    points = models.IntegerField(
        default=10, validators=[MinValueValidator(1)], verbose_name="Бали"
    )
    order = models.IntegerField(
        validators=[MinValueValidator(1)], verbose_name="Порядок"
    )
    is_ai_generated = models.BooleanField(default=False, verbose_name="Згенеровано")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Вправа"
        verbose_name_plural = "Вправи"
        db_table = "exercises"
        ordering = ["order"]

    def __str__(self):
        if self.lesson:
            return f"{self.lesson.title} - {self.get_exercise_type_display()}"
        return f"Test: {self.course_test.course.title} - {self.get_exercise_type_display()}"


class UserLessonProgress(models.Model):
    """Прогрес користувача по уроку"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="lesson_progress",
        verbose_name="Користувач",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="user_progress",
        verbose_name="Урок",
    )
    is_completed = models.BooleanField(default=False, verbose_name="Завершено")
    score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Оцінка",
    )
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Завершено о"
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Почато о")

    class Meta:
        verbose_name = "Прогрес по уроку"
        verbose_name_plural = "Прогрес по уроках"
        db_table = "user_lesson_progress"
        unique_together = ["user", "lesson"]

    def __str__(self):
        return f"{self.user.username} - {self.lesson.title}"


class UserExerciseAttempt(models.Model):
    """Спроба виконання вправи користувачем"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="exercise_attempts",
        verbose_name="Користувач",
    )
    exercise = models.ForeignKey(
        Exercise,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Вправа",
    )
    user_answer = models.TextField(verbose_name="Відповідь користувача")
    is_correct = models.BooleanField(verbose_name="Правильно")
    ai_feedback = models.TextField(null=True, blank=True, verbose_name="Відгук")
    points_earned = models.IntegerField(default=0, verbose_name="Отримано балів")
    attempted_at = models.DateTimeField(auto_now_add=True, verbose_name="Спробовано о")

    class Meta:
        verbose_name = "Спроба вправи"
        verbose_name_plural = "Спроби вправ"
        db_table = "user_exercise_attempts"
        ordering = ["-attempted_at"]

    def __str__(self):
        return f'{self.user.username} - {self.exercise} - {"✓" if self.is_correct else "✗"}'


class UserCourseProgress(models.Model):
    """Прогрес користувача по курсу"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="course_progress",
        verbose_name="Користувач",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="user_progress",
        verbose_name="Курс",
    )
    is_completed = models.BooleanField(default=False, verbose_name="Завершено")
    test_score = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name="Бал за тест",
    )
    test_passed = models.BooleanField(default=False, verbose_name="Тест складено")
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Завершено о"
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Почато о")

    class Meta:
        verbose_name = "Прогрес по курсу"
        verbose_name_plural = "Прогрес по курсах"
        db_table = "user_course_progress"
        unique_together = ["user", "course"]

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"
