"""
URL configuration for language_learning project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Allauth
    path('accounts/', include('allauth.urls')),
    
    # Home page
    path('', TemplateView.as_view(template_name='home.html'), name='home'),

    
    # Template views
    path('courses/', include(('courses.urls', 'courses'), namespace='courses')),
    path('users/', include(('users.urls', 'users'), namespace='users')),
    path('tests/', include(('tests.urls', 'tests'), namespace='tests')),
    
    # API endpoints
    path('api/courses/', include(('courses.urls', 'courses'), namespace='courses_api')),
    path('api/users/', include(('users.urls', 'users'), namespace='users_api')),
    path('api/ai/', include('ai_services.urls')),
    path('api/tests/', include(('tests.urls', 'tests'), namespace='tests_api')),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
