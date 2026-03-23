from django.contrib import admin
from .models import (
    Course,
    Lesson,
    Exercise,
    UserLessonProgress,
    UserExerciseAttempt,
    CourseTest,
)


@admin.register(CourseTest)
class CourseTestAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "passing_score", "created_at"]
    list_filter = ["course"]
    search_fields = ["title"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["title", "language", "level", "is_active", "created_at"]
    list_filter = ["language", "level", "is_active"]
    search_fields = ["title", "description"]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "order", "is_active", "created_at"]
    list_filter = ["course", "is_active"]
    search_fields = ["title", "description"]


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ["lesson", "exercise_type", "order", "points", "is_ai_generated"]
    list_filter = ["exercise_type", "is_ai_generated", "lesson__course"]
    search_fields = ["question"]


@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(admin.ModelAdmin):
    list_display = ["user", "lesson", "is_completed", "score", "completed_at"]
    list_filter = ["is_completed", "lesson__course"]
    search_fields = ["user__username", "lesson__title"]


@admin.register(UserExerciseAttempt)
class UserExerciseAttemptAdmin(admin.ModelAdmin):
    list_display = ["user", "exercise", "is_correct", "points_earned", "attempted_at"]
    list_filter = ["is_correct", "exercise__lesson__course"]
    search_fields = ["user__username"]
