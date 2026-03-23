import os

path = r"c:\Users\myhai\OneDrive\Desktop\Diplom Project\backend\tests\views.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace block 1
old_block_1 = """        if question.question_type in ['essay', 'short_answer']:
            ai_service = AIExerciseService()
            is_correct = ai_service.check_answer_with_ai(
                question.question_text,
                question.correct_answer,
                user_answer
            )
            ai_feedback = ai_service.get_feedback(
                question.question_text,
                question.correct_answer,
                user_answer,
                question.question_type
            )"""

new_block_1 = """        if question.question_type in ['essay', 'short_answer']:
            ai_service = AIExerciseService()
            ai_result = ai_service.check_answer_and_get_feedback(
                question.question_text,
                question.correct_answer,
                user_answer,
                question.question_type
            )
            is_correct = ai_result['is_correct']
            ai_feedback = ai_result['feedback']"""

# Replace block 2
old_block_2 = """        if question.question_type in ['essay', 'short_answer']:
            ai_service = AIExerciseService()
            is_correct = ai_service.check_answer_with_ai(
                question.question_text,
                question.correct_answer,
                user_answer
            )
            ai_feedback = ai_service.get_feedback(
                question.question_text,
                question.correct_answer,
                user_answer,
                question.question_type
            )"""
# (They are identical)

# Try replacing with re for flexibility with whitespace if exact match fails
import re

pattern = r"if question\.question_type in \['essay', 'short_answer'\]:\s+ai_service = AIExerciseService\(\)\s+is_correct = ai_service\.check_answer_with_ai\(\s+question\.question_text,\s+question\.correct_answer,\s+user_answer\s+\)\s+ai_feedback = ai_service\.get_feedback\(\s+question\.question_text,\s+question\.correct_answer,\s+user_answer,\s+question\.question_type\s+\)"

new_content = re.sub(
    pattern, new_block_1.replace("        ", "            "), content
)  # Adjust indent if needed

# If re fails, try simple replace
if new_content == content:
    new_content = content.replace(old_block_1, new_block_1)

# Check if anything changed
if new_content != content:
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Success")
else:
    print("Match not found")
