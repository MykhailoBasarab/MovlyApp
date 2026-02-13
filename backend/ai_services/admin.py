from django.contrib import admin
from .models import AIInteraction, LearningAnalytics


@admin.register(AIInteraction)
class AIInteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'interaction_type', 'tokens_used', 'created_at']
    list_filter = ['interaction_type', 'created_at']
    search_fields = ['user__username', 'prompt']


@admin.register(LearningAnalytics)
class LearningAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'exercises_completed', 'lessons_completed', 'accuracy_rate']
    list_filter = ['date']
    search_fields = ['user__username']

