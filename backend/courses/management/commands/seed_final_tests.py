from django.core.management.base import BaseCommand
from courses.models import Course, CourseTest, Exercise
from ai_services.services import AIExerciseService
import time
import random

class Command(BaseCommand):
    help = 'Seeds final tests for all courses with AI-generated questions'

    def handle(self, *args, **options):
        courses = Course.objects.all()
        ai_service = AIExerciseService()

        exercise_types = ['multiple_choice', 'fill_blank']

        for course in courses:
            self.stdout.write(f'Processing course: {course.title}...')
            
            # Ensure the Final Test object exists
            test, created = CourseTest.objects.get_or_create(
                course=course,
                defaults={
                    'title': f'Фінальний тест: {course.title}',
                    'description': f'Заключний іспит для перевірки знань за весь курс: {course.title}.',
                    'passing_score': 80
                }
            )

            # Check if it already has real questions (not placeholders)
            existing_questions = test.questions.all()
            if existing_questions.count() > 0:
                # Basic check for placeholders (like the ones user showed)
                if 'Test Question' in existing_questions[0].question:
                    self.stdout.write(f'Deleting placeholders for {course.title}...')
                    existing_questions.delete()
                else:
                    self.stdout.write(f'Test for {course.title} already has {existing_questions.count()} questions. Skipping...')
                    continue
            
            # Generate 5 questions (mix of types)
            questions_to_generate = 5
            for i in range(questions_to_generate):
                ex_type = random.choice(exercise_types)
                self.stdout.write(f'  Generating question {i+1} ({ex_type})...')
                
                # Use Course title as topic for final test context
                # and maybe add "final exam" context
                topic = f'Final exam covering all aspects of {course.title}'
                
                # Add a bit of delay if needed for rate limits, but AI service uses gpt-3.5 usually
                # result = ai_service.generate_exercise(topic, ex_type, course.language, course.level)
                
                # Mock high-quality fallback if AI fails (or as default for this script)
                # But we have AI key, so let's try to use it
                try:
                    result = ai_service.generate_exercise(topic, ex_type, course.language, course.level)
                    if result:
                        Exercise.objects.create(
                            course_test=test,
                            exercise_type=ex_type,
                            question=result['question'],
                            correct_answer=result['correct_answer'],
                            options=result.get('options'),
                            points=20, # 5 questions * 20 = 100 points
                            order=i+1,
                            is_ai_generated=True
                        )
                    else:
                        self.stderr.write(f'  Failed to generate question {i+1} for {course.title}')
                except Exception as e:
                    self.stderr.write(f'  Error generating: {e}')
            
            self.stdout.write(self.style.SUCCESS(f'Successfully seeded test for {course.title}'))
