from django.contrib import admin
from django.contrib.sites.models import Site

from allauth.socialaccount.models import SocialAccount, SocialApp, SocialToken

admin.site.unregister(Site)
admin.site.unregister(SocialApp)
admin.site.unregister(SocialAccount)
admin.site.unregister(SocialToken)
