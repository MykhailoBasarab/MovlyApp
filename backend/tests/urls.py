from django.urls import path
from . import views

app_name = 'tests'

urlpatterns = [
    # Template views
    path('', views.tests_list_view, name='tests-list'),
    path('<int:pk>/', views.test_detail_view, name='test-detail'),
    path('<int:pk>/start/', views.start_test_view, name='start-test'),
    path('attempt/<int:pk>/', views.test_attempt_view, name='test-attempt'),
    path('attempt/<int:attempt_id>/question/<int:question_id>/submit/', views.submit_test_answer_view, name='submit-test-answer'),
    path('attempt/<int:pk>/complete/', views.complete_test_view, name='complete-test'),
    
    # API endpoints
    path('types/', views.TestTypeListView.as_view(), name='api-test-type-list'),
    path('', views.TestListView.as_view(), name='api-test-list'),
    path('<int:pk>/', views.TestDetailView.as_view(), name='api-test-detail'),
    path('<int:pk>/start/', views.StartTestView.as_view(), name='api-start-test'),
    path('attempts/<int:pk>/', views.TestAttemptDetailView.as_view(), name='api-attempt-detail'),
    path('attempts/<int:pk>/sections/<int:section_id>/', views.SectionQuestionsView.as_view(), name='api-section-questions'),
    path('attempts/<int:pk>/answer/', views.SubmitAnswerView.as_view(), name='api-submit-answer'),
    path('attempts/<int:pk>/complete/', views.CompleteTestView.as_view(), name='api-complete-test'),
    path('attempts/<int:pk>/generate-audio/', views.GenerateAudioView.as_view(), name='api-generate-audio'),
]
