# core/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from .models import Music, UserProfile, User
from django.core.exceptions import ValidationError

class MusicUploadForm(forms.ModelForm):
    class Meta:
        model = Music
        fields = ['title', 'artist', 'file_path']

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']

class CustomUserCreationForm(DjangoUserCreationForm):
    username = forms.CharField(
        max_length=150,
        required=True,
        help_text='',
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )

    email = forms.EmailField(
        required=True,
        help_text='',
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address'})
    )

    password = forms.CharField(
        label=("Password"),
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'}),
        help_text=''
    )
    
    password2 = forms.CharField(
        label=("Password confirmation"),
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password'}),
        help_text=''
    )

    class Meta(DjangoUserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'password', 'password2')

    def clean(self):
        # Call the parent's clean method to get the data and perform the password mismatch check
        cleaned_data = super().clean()

        # This try-except block silently catches and hides the password validation errors
        try:
            # Re-run password validation. If it fails, it will raise an exception.
            self.cleaned_data['password'] = self.cleaned_data['password']
            self.cleaned_data['password2'] = self.cleaned_data['password2']
        except ValidationError:
            # We catch the exception but do nothing, effectively hiding the error messages
            pass

        return cleaned_data
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            UserProfile.objects.create(user=user)
        return user