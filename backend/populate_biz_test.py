import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'language_learning.settings')
django.setup()

from courses.models import Course, CourseTest, Exercise

def populate():
    course_title = "Business English: Mastering Professionalism"
    try:
        course = Course.objects.get(title=course_title)
    except Course.DoesNotExist:
        print(f"Error: Course '{course_title}' not found.")
        return

    # Delete existing test and exercises to start fresh
    CourseTest.objects.filter(course=course).delete()

    test = CourseTest.objects.create(
        course=course,
        title=f"Фінальний тест: {course_title}",
        description="Перевірте свої знання ділової англійської мови: від професійної лексики до ділового етикету та листування. Цей тест допоможе вам переконатися, що ви засвоїли всі ключові аспекти курсу.",
        passing_score=80
    )

    questions = [
        {
            "type": "multiple_choice",
            "question": "Which of the following is the most appropriate formal closing for a business email when you don't know the recipient's name?",
            "correct": "Yours faithfully",
            "options": ["Cheers", "Best regards", "Yours faithfully", "Talk soon"],
            "points": 10,
            "order": 1
        },
        {
            "type": "fill_blank",
            "question": "I am looking forward ___ (to) meeting you next week. Fill in the missing preposition.",
            "correct": "to",
            "points": 10,
            "order": 2
        },
        {
            "type": "multiple_choice",
            "question": "In a professional context, what does the acronym 'BCC' stand for in an email header?",
            "correct": "Blind Carbon Copy",
            "options": ["Business Carbon Copy", "Blind Carbon Copy", "Basic Communication Code", "Brief Corporate Chat"],
            "points": 10,
            "order": 3
        },
        {
            "type": "fill_blank",
            "question": "Could you please ___ (send) me the latest sales report by the end of the day? Fill in the missing verb.",
            "correct": "send",
            "points": 10,
            "order": 4
        },
        {
            "type": "multiple_choice",
            "question": "When scheduling a meeting or an event, what does 'TBA' usually mean?",
            "correct": "To Be Announced",
            "options": ["To Be Announced", "Totally Basic Agreement", "Time Between Acts", "Technical Board Assessment"],
            "points": 10,
            "order": 5
        },
        {
            "type": "multiple_choice",
            "question": "Which of these words is a synonym for 'postpone' in a business setting?",
            "correct": "Defer",
            "options": ["Advance", "Defer", "Hasten", "Implement"],
            "points": 10,
            "order": 6
        },
        {
            "type": "fill_blank",
            "question": "We need to hammer ___ (out) the final details of the contract before signing. Fill in the missing particle.",
            "correct": "out",
            "points": 10,
            "order": 7
        },
        {
            "type": "multiple_choice",
            "question": "Which phrase is commonly used to start a formal business meeting?",
            "correct": "Let's get down to business.",
            "options": ["What's up guys?", "Let's get down to business.", "Why are we here?", "Tell me a joke."],
            "points": 10,
            "order": 8
        },
        {
            "type": "fill_blank",
            "question": "I'm sorry, I didn't quite catch that. Could you please ___ (repeat) what you just said? Fill in the missing verb.",
            "correct": "repeat",
            "points": 10,
            "order": 9
        },
        {
            "type": "multiple_choice",
            "question": "What does the abbreviation 'EOD' stand for in business communication?",
            "correct": "End Of Day",
            "options": ["End Of Day", "Each Other's Data", "Early Out Draft", "Electronic Office Document"],
            "points": 10,
            "order": 10
        }
    ]

    for q in questions:
        Exercise.objects.create(
            course_test=test,
            exercise_type=q["type"],
            question=q["question"],
            correct_answer=q["correct"],
            options=q.get("options"),
            points=q["points"],
            order=q["order"]
        )
    
    print(f"Successfully populated {len(questions)} questions for '{course_title}' test.")

if __name__ == "__main__":
    populate()
