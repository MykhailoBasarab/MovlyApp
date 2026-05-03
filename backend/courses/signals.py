from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserExerciseAttempt, Exercise
from users.models import UserWord

@receiver(post_save, sender=UserExerciseAttempt)
def add_to_vocabulary(sender, instance, created, **kwargs):
    """
    Автоматично додає слово до словника користувача після правильної відповіді у вправі.
    """
    if created and instance.is_correct:
        exercise = instance.exercise
        user = instance.user
        
        # Визначаємо мову та курс
        language = "en" 
        course = None
        if exercise.lesson and exercise.lesson.course:
            language = exercise.lesson.course.language
            course = exercise.lesson.course
        elif exercise.course_test and exercise.course_test.course:
            language = exercise.course_test.course.language
            course = exercise.course_test.course

        # Тільки для певних типів вправ, де можна чітко виділити слово та переклад
        if exercise.exercise_type in ['translation', 'multiple_choice', 'fill_blank']:
            word_text = exercise.question.strip()
            translation_text = exercise.correct_answer.strip()
            
            if len(word_text) < 100:
                uw, created = UserWord.objects.get_or_create(
                    user=user,
                    word=word_text,
                    language=language,
                    defaults={
                        'translation': translation_text,
                        'course': course
                    }
                )
                
                if created:
                    from django.urls import reverse
                    from users.models import Notification
                    Notification.objects.create(
                        user=user,
                        title="Нове слово! 📖",
                        message=f"Слово '{word_text}' додано до вашого словника.",
                        notification_type='info',
                        link=reverse("users:vocabulary")
                    )
