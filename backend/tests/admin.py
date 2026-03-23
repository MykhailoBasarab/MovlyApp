from django.contrib import admin

from .models import Test, TestAnswer, TestAttempt, TestQuestion, TestSection, TestType


@admin.register(TestType)
class TestTypeAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "duration_minutes", "total_score"]
    search_fields = ["name", "code"]


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "test_type",
        "language",
        "level",
        "is_active",
        "created_at",
    ]
    list_filter = ["test_type", "language", "level", "is_active"]
    search_fields = ["title", "description"]


@admin.register(TestSection)
class TestSectionAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "test",
        "section_type",
        "duration_minutes",
        "max_score",
        "order",
    ]
    list_filter = ["section_type", "test"]
    search_fields = ["title"]


@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ["section", "question_type", "order", "points", "is_ai_generated"]
    list_filter = ["question_type", "is_ai_generated", "section__test"]
    search_fields = ["question_text"]


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "test",
        "status",
        "total_score",
        "started_at",
        "completed_at",
    ]
    list_filter = ["status", "test__test_type"]
    search_fields = ["user__username", "test__title"]


@admin.register(TestAnswer)
class TestAnswerAdmin(admin.ModelAdmin):
    list_display = ["attempt", "question", "is_correct", "points_earned", "answered_at"]
    list_filter = ["is_correct", "question__section__test"]
    search_fields = ["user_answer"]
