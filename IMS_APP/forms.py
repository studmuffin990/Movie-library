from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Movie


class SignUpForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username',)


class MovieForm(forms.ModelForm):
    class Meta:
        model = Movie
        fields = [
            'movie_title',
            'genre',
            'director',
            'release_year',
            'release_date',
            'rating',
            'description',
            'status',
        ]
        widgets = {
            'movie_title': forms.TextInput(attrs={'placeholder': 'e.g. Inception'}),
            'genre': forms.TextInput(attrs={'placeholder': 'e.g. Sci-Fi'}),
            'director': forms.TextInput(attrs={'placeholder': 'e.g. Christopher Nolan'}),
            'release_year': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
            'release_date': forms.DateInput(attrs={'type': 'date'}),
            'rating': forms.NumberInput(attrs={'step': '0.1', 'min': '0', 'max': '10'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write a short overview of the movie...'}),
            'status': forms.Select(),
        }
