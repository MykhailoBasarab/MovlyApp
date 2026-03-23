from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    """Форма реєстрації користувача"""

    email = forms.EmailField(
        required=True,
        label="Email",
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )

    class Meta:
        model = CustomUser
        fields = ("username", "email", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update({"class": "form-control"})
        self.fields["password2"].widget.attrs.update({"class": "form-control"})


class LoginForm(forms.Form):
    """Форма входу"""

    username = forms.CharField(
        label="Ім'я користувача",
        widget=forms.TextInput(attrs={"class": "form-control", "autofocus": True}),
    )
    password = forms.CharField(
        label="Пароль", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )


class UserProfileForm(forms.ModelForm):
    """Форма редагування профілю користувача"""

    class Meta:
        model = CustomUser
        fields = (
            "username",
            "email",
            "native_language",
            "learning_language",
            "level",
            "avatar",
        )
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "native_language": forms.Select(attrs={"class": "form-control"}),
            "learning_language": forms.Select(attrs={"class": "form-control"}),
            "level": forms.Select(attrs={"class": "form-control"}),
            "avatar": forms.FileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
        }
