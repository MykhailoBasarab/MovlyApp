from django import forms

from .models import Test


class TestFilterForm(forms.Form):

    language = forms.ChoiceField(
        choices=[
            ("", "Всі мови"),
            ("en", "English"),
            ("de", "Deutsch"),
            ("fr", "Français"),
            ("es", "Español"),
            ("it", "Italiano"),
            ("pl", "Polski"),
        ],
        required=False,
        label="Мова",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    level = forms.ChoiceField(
        choices=[
            ("", "Всі рівні"),
            ("beginner", "Початковий"),
            ("elementary", "Елементарний"),
            ("intermediate", "Середній"),
            ("upper_intermediate", "Вище середнього"),
            ("advanced", "Просунутий"),
        ],
        required=False,
        label="Рівень",
        widget=forms.Select(attrs={"class": "form-control"}),
    )


class TestAnswerForm(forms.Form):

    answer = forms.CharField(
        label="Ваша відповідь",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        required=True,
    )


class MultipleChoiceTestForm(forms.Form):
    answer = forms.ChoiceField(
        label="Виберіть відповідь",
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        required=True,
    )

    def __init__(self, *args, options=None, **kwargs):
        super().__init__(*args, **kwargs)
        if options:
            self.fields["answer"].choices = [(opt, opt) for opt in options]
