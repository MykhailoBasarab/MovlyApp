import os

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views import View

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import AIExerciseService


class GenerateExerciseView(APIView):
    """Генерація вправи"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        lesson_topic = request.data.get("lesson_topic")
        exercise_type = request.data.get("exercise_type", "multiple_choice")
        language = request.data.get("language", "en")
        level = request.data.get("level", "beginner")

        if not lesson_topic:
            return Response(
                {"error": "Не вказано тему уроку"}, status=status.HTTP_400_BAD_REQUEST
            )

        ai_service = AIExerciseService()
        exercise = ai_service.generate_exercise(
            lesson_topic, exercise_type, language, level
        )

        if not exercise:
            return Response(
                {"error": "Не вдалося згенерувати вправу"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(exercise)


class GetFeedbackView(APIView):
    """Отримання відгуку"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        question = request.data.get("question")
        correct_answer = request.data.get("correct_answer")
        user_answer = request.data.get("user_answer")
        exercise_type = request.data.get("exercise_type", "multiple_choice")

        if not all([question, correct_answer, user_answer]):
            return Response(
                {"error": "Не всі необхідні поля заповнені"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        ai_service = AIExerciseService()
        feedback = ai_service.get_feedback(
            question, correct_answer, user_answer, exercise_type
        )

        if not feedback:
            return Response(
                {"error": "Не вдалося отримати відгук"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({"feedback": feedback})
