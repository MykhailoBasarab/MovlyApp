"""
URL configuration for language_learning project.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from courses.views import home_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("", home_view, name="home"),
    path("courses/", include(("courses.urls", "courses"), namespace="courses")),
    path("users/", include(("users.urls", "users"), namespace="users")),
    path("tests/", include(("tests.urls", "tests"), namespace="tests")),
    path("api/ai/", include("ai_services.urls")),
    path("api/tests/", include(("tests.urls", "tests"), namespace="tests_api")),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
