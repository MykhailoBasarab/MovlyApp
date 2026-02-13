from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser, UserProgress


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'native_language', 'learning_language', 'level', 'created_at']
    list_filter = ['level', 'native_language', 'learning_language', 'is_staff']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Додаткова інформація', {
            'fields': ('native_language', 'learning_language', 'level', 'avatar')
        }),
    )


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_lessons_completed', 'total_exercises_completed', 'current_streak', 'total_xp']
    list_filter = ['last_activity_date']

