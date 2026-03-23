from django.urls import path

from . import views

app_name = "courses"

urlpatterns = [
    path("", views.courses_list_view, name="courses-list"),
    path("mistakes/", views.mistakes_list_view, name="mistakes-list"),
    path("<int:pk>/", views.course_detail_view, name="course-detail"),
    path("lessons/<int:pk>/", views.lesson_detail_view, name="lesson-detail"),
    path(
        "exercises/<int:pk>/submit/", views.submit_exercise_view, name="submit-exercise"
    ),
    path(
        "lessons/<int:pk>/complete/", views.complete_lesson_view, name="complete-lesson"
    ),
    path("<int:pk>/test/", views.course_test_start_view, name="course-test-start"),
    path("<int:pk>/test/take/", views.course_test_take_view, name="course-test-take"),
    path("api/", views.CourseListView.as_view(), name="api-course-list"),
    path("api/<int:pk>/", views.CourseDetailView.as_view(), name="api-course-detail"),
    path(
        "api/lessons/<int:pk>/",
        views.LessonDetailView.as_view(),
        name="api-lesson-detail",
    ),
    path(
        "api/exercises/<int:pk>/submit/",
        views.SubmitExerciseView.as_view(),
        name="api-submit-exercise",
    ),
    path(
        "api/lessons/<int:pk>/complete/",
        views.CompleteLessonView.as_view(),
        name="api-complete-lesson",
    ),
]
