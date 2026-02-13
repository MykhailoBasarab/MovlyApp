from django import forms
from .models import Exercise


class ExerciseAnswerForm(forms.Form):
    """Форма для відповіді на вправу"""
    answer = forms.CharField(
        label='Ваша відповідь',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введіть відповідь'}),
        required=True
    )


class MultipleChoiceForm(forms.Form):
    """Форма для вибору відповіді"""
    answer = forms.ChoiceField(
        label='Виберіть відповідь',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        required=True
    )

    def __init__(self, *args, options=None, **kwargs):
        super().__init__(*args, **kwargs)
        if options:
            self.fields['answer'].choices = [(opt, opt) for opt in options]


class FilterForm(forms.Form):
    """Форма фільтрації курсів"""
    language = forms.ChoiceField(
        choices=[
            ('', 'Всі мови'),
            ('en', 'English'),
            ('de', 'Deutsch'),
            ('fr', 'Français'),
            ('es', 'Español'),
            ('it', 'Italiano'),
        ],
        required=False,
        label='Мова',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    level = forms.ChoiceField(
        choices=[
            ('', 'Всі рівні'),
            ('beginner', 'Початковий'),
            ('elementary', 'Елементарний'),
            ('intermediate', 'Середній'),
            ('upper_intermediate', 'Вище середнього'),
            ('advanced', 'Просунутий'),
        ],
        required=False,
        label='Рівень',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

