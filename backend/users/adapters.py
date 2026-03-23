from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Connect existing users by email automatically if the social account email matches.
        """
        # If the social account is already connected to a user, do nothing
        if sociallogin.is_existing:
            return

        # Check if the email is provided by the social provider
        email = sociallogin.account.extra_data.get("email")
        if not email:
            return

        email = email.lower()
        User = get_user_model()

        # Try to find a user with the same email
        # Use .filter().first() instead of .get() to avoid MultipleObjectsReturned if data is corrupted
        user = User.objects.filter(email__iexact=email).first()
        if user:
            # If user exists, connect the social account to this user
            if not sociallogin.is_existing:
                sociallogin.connect(request, user)
