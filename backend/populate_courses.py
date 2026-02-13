
import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'language_learning.settings')
django.setup()

from courses.models import Course, Lesson, Exercise, CourseTest

def clear_data():
    print("Clearing old course data...")
    Course.objects.all().delete()

def create_advanced_english():
    print("Creating Business English Course...")
    course = Course.objects.create(
        title='Business English: Mastering Professionalism',
        description='Підвищіть свій професійний рівень. Курс фокусується на діловому листуванні, переговорах та презентаціях.',
        language='en',
        level='intermediate',
        is_active=True
    )

    lessons = [
        {
            'title': 'The Art of Business Correspondence',
            'description': 'Навчіться писати професійні імейли, які отримують відповіді.',
            'content': """
                <h3>Effective Email Structure</h3>
                <p>Professional emails follow a specific hierarchy: Subject line, Greeting, Opening, Body, Call to Action, and Closing.</p>
                <ul>
                    <li><strong>Formal Greeting:</strong> "Dear Mr./Ms. [Surname],"</li>
                    <li><strong>Expressing Purpose:</strong> "I am writing to inquire about..." or "I am reaching out regarding..."</li>
                    <li><strong>Next Steps:</strong> "I look forward to hearing from you."</li>
                </ul>
            """,
            'exercises': [
                {
                    'type': 'multiple_choice',
                    'q': 'Which greeting is most appropriate for a formal business letter to someone you don\'t know?',
                    'ans': 'Dear Sir/Madam,',
                    'opts': ['Hi there!', 'Dear Sir/Madam,', 'Hey!', 'To whom it may concern,'],
                    'pts': 15
                },
                {
                    'type': 'fill_blank',
                    'q': 'I am writing to ___ you about the upcoming meeting.',
                    'ans': 'inform',
                    'pts': 10
                }
            ]
        },
        {
            'title': 'Negotiation Tactics & Psychology',
            'description': 'Як досягати вигідних умов у ділових зустрічах.',
            'content': """
                <h3>Key Negotiation Phrases</h3>
                <p>Negotiation is about finding common ground while maintaining your position.</p>
                <ul>
                    <li><strong>Proposing:</strong> "Would you be willing to consider...?"</li>
                    <li><strong>Counter-offering:</strong> "I understand your point, however, our budget is limited to..."</li>
                    <li><strong>Closing the deal:</strong> "That sounds like a fair compromise. Let's wrap this up."</li>
                </ul>
            """,
            'exercises': [
                {
                    'type': 'multiple_choice',
                    'q': 'What does "common ground" mean in a negotiation?',
                    'ans': 'Areas of mutual agreement',
                    'opts': ['Areas of mutual agreement', 'The floor of the meeting room', 'A fight', 'A price increase'],
                    'pts': 20
                }
            ]
        }
    ]

    for i, l_data in enumerate(lessons, 1):
        lesson = Lesson.objects.create(
            course=course,
            title=l_data['title'],
            description=l_data['description'],
            content=l_data['content'],
            order=i
        )
        for j, ex in enumerate(l_data['exercises'], 1):
            Exercise.objects.create(
                lesson=lesson,
                exercise_type=ex['type'],
                question=ex['q'],
                correct_answer=ex['ans'],
                options=ex.get('opts'),
                points=ex['pts'],
                order=j
            )

def create_grammar_intensive():
    print("Creating Grammar Intensive Course...")
    course = Course.objects.create(
        title='English Grammar: The Hard Parts',
        description='Інтенсивний курс по найскладнішим темам англійської граматики: Conditionals, Passive Voice та Phrasal Verbs.',
        language='en',
        level='upper_intermediate',
        is_active=True
    )

    lessons = [
        {
            'title': 'Mastering Conditionals (0, 1, 2, 3)',
            'description': 'Як говорити про гіпотетичні ситуації без помилок.',
            'content': """
                <h3>The Third Conditional</h3>
                <p>Used to talk about imaginary situations in the past and their imaginary results.</p>
                <p><strong>Structure:</strong> If + Past Perfect, would have + Past Participle</p>
                <p><em>Example:</em> If I had studied harder, I would have passed the exam.</p>
            """,
            'exercises': [
                {
                    'type': 'fill_blank',
                    'q': 'If I ___ (know) you were coming, I would have baked a cake.',
                    'ans': 'had known',
                    'pts': 25
                }
            ]
        }
    ]

    for i, l_data in enumerate(lessons, 1):
        lesson = Lesson.objects.create(
            course=course,
            title=l_data['title'],
            description=l_data['description'],
            content=l_data['content'],
            order=i
        )
        for j, ex in enumerate(l_data['exercises'], 1):
            Exercise.objects.create(
                lesson=lesson,
                exercise_type=ex['type'],
                question=ex['q'],
                correct_answer=ex['ans'],
                options=ex.get('opts'),
                points=ex['pts'],
                order=j
            )

def create_german_travel():
    print("Creating German Travel Course...")
    course = Course.objects.create(
        title='Deutsch für Reisende (Німецька для мандрівників)',
        description='Все, що вам потрібно знати для комфортної подорожі Німеччиною, Австрією чи Швейцарією.',
        language='de',
        level='beginner',
        is_active=True
    )

    lessons = [
        {
            'title': 'Im Restaurant (В ресторані)',
            'description': 'Як замовити їжу та попросити рахунок.',
            'content': """
                <h3>Німецька на практиці</h3>
                <ul>
                    <li><strong>Ich hätte gerne...</strong> - Я хотів би...</li>
                    <li><strong>Die Speisekarte, bitte.</strong> - Меню, будь ласка.</li>
                    <li><strong>Zahlen, bitte!</strong> - Рахунок, будь ласка!</li>
                    <li><strong>Ist dieser Tisch frei?</strong> - Цей столик вільний?</li>
                </ul>
            """,
            'exercises': [
                {
                    'type': 'multiple_choice',
                    'q': 'Як ввічливо попросити рахунок?',
                    'ans': 'Zahlen, bitte!',
                    'opts': ['Zahlen, bitte!', 'Hallo!', 'Guten Tag', 'Ich bin fertig'],
                    'pts': 15
                }
            ]
        }
    ]

    for i, l_data in enumerate(lessons, 1):
        lesson = Lesson.objects.create(
            course=course,
            title=l_data['title'],
            description=l_data['description'],
            content=l_data['content'],
            order=i
        )
        for j, ex in enumerate(l_data['exercises'], 1):
            Exercise.objects.create(
                lesson=lesson,
                exercise_type=ex['type'],
                question=ex['q'],
                correct_answer=ex['ans'],
                options=ex.get('opts'),
                points=ex['pts'],
                order=j
            )

if __name__ == '__main__':
    clear_data()
    create_advanced_english()
    create_grammar_intensive()
    create_german_travel()
    print("Database population finished successfully with premium-grade content!")
