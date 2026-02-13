import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'language_learning.settings')
django.setup()

from courses.models import Course, Lesson, Exercise, CourseTest
from users.models import Badge

def seed_data():
    badges_data = [
        {
            'name': 'Перші кроки',
            'description': 'Завершено перший курс',
            'icon': 'fas fa-baby-carriage',
            'criteria_type': 'course_completed',
            'criteria_value': 1
        },
        {
            'name': 'Майстер Англійської',
            'description': 'Завершено базовий курс англійської',
            'icon': 'fas fa-graduation-cap',
            'criteria_type': 'course_completed',
            'criteria_value': 2
        },
        {
            'name': 'Поліглот',
            'description': 'Завершено 3 курси',
            'icon': 'fas fa-language',
            'criteria_type': 'course_completed',
            'criteria_value': 3
        },
        {
            'name': 'XP Монстр',
            'description': 'Досягнуто 5000 XP',
            'icon': 'fas fa-dragon',
            'criteria_type': 'xp_reached',
            'criteria_value': 5000
        }
    ]

    for b_data in badges_data:
        Badge.objects.get_or_create(name=b_data['name'], defaults=b_data)

    courses_to_create = [
        {
            'title': 'English for Travelers',
            'description': 'Practical English for your next trip abroad. Learn how to order food, ask for directions, and more.',
            'language': 'en',
            'level': 'elementary'
        },
        {
            'title': 'Business German Basics',
            'description': 'Essential vocabulary and phrases for working in a German-speaking environment.',
            'language': 'de',
            'level': 'intermediate'
        },
        {
            'title': 'French Gastronomy 101',
            'description': 'Learn French while exploring its world-famous cuisine. Vocabulary for restaurants and cooking.',
            'language': 'fr',
            'level': 'beginner'
        },
        {
            'title': 'Spanish Connection',
            'description': 'Connect with millions of speakers. Basic Spanish for daily conversations.',
            'language': 'es',
            'level': 'beginner'
        }
    ]

    for c_data in courses_to_create:
        course, created = Course.objects.get_or_create(title=c_data['title'], defaults=c_data)
        if created:
            for i in range(1, 4):
                lesson = Lesson.objects.create(
                    course=course,
                    title=f'Lesson {i} of {course.title}',
                    description=f'Description for lesson {i}',
                    order=i,
                    content=f'<h3>Welcome to Lesson {i}</h3><p>This is where you learn important stuff about {course.language}.</p><ul><li>Topic A</li><li>Topic B</li></ul>'
                )
                
                Exercise.objects.create(
                    lesson=lesson,
                    exercise_type='multiple_choice',
                    question=f'What is the meaning of life in {course.title}?',
                    correct_answer='Learning',
                    options=['Eating', 'Sleeping', 'Learning', 'Coding'],
                    points=10,
                    order=1
                )
                Exercise.objects.create(
                    lesson=lesson,
                    exercise_type='translation',
                    question='Translate: "Hello"',
                    correct_answer='Привіт',
                    points=20,
                    order=2
                )

            test = CourseTest.objects.create(
                course=course,
                title=f'Final Test: {course.title}',
                description='Show what you have learned!',
                passing_score=70
            )
            
            for i in range(1, 6):
                Exercise.objects.create(
                    course_test=test,
                    exercise_type='multiple_choice',
                    question=f'Test Question {i} for {course.title}',
                    correct_answer='Option A',
                    options=['Option A', 'Option B', 'Option C', 'Option D'],
                    points=20,
                    order=i
                )

    print("Data seeding completed successfully!")

if __name__ == "__main__":
    seed_data()
