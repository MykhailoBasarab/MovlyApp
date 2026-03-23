from django.urls import path

from . import views

app_name = "ai_services"

urlpatterns = [
    path(
        "generate-exercise/",
        views.GenerateExerciseView.as_view(),
        name="generate-exercise",
    ),
    path("get-feedback/", views.GetFeedbackView.as_view(), name="get-feedback"),
]
