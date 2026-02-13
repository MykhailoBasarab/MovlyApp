import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'language_learning.settings')
django.setup()

from courses.models import Course

def add_new_course():
    course, created = Course.objects.get_or_create(
        title='Французька для мандрівників',
        defaults={
            'description': 'Дізнайтеся основні фрази та граматику для вашої наступної подорожі до Парижа. Від замовлення круасанів до орієнтування в метро.',
            'language': 'fr',
            'level': 'beginner',
            'is_active': True
        }
    )
    if created:
        print(f"Курс '{course.title}' успішно створено!")
    else:
        print(f"Курс '{course.title}' вже існує.")

if __name__ == '__main__':
    add_new_course()
