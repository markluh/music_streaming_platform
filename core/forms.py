# core/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from .models import Music, UserProfile, User

# The form used for uploading music files
class MusicUploadForm(forms.ModelForm):
    """
    A form for uploading music.
    It automatically generates fields from the Music model.
    """
    class Meta:
        model = Music
        fields = ['title', 'artist', 'file_path']

# The form used for updating a user's profile picture
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['profile_picture']

# A form for user registration, which includes an email field
class CustomUserCreationForm(DjangoUserCreationForm):
    email = forms.EmailField(
        required=True,
        help_text='Required. Please enter a valid email address.',
        widget=forms.EmailInput(attrs={'placeholder': 'Email Address'})
    )

    class Meta(DjangoUserCreationForm.Meta):
        model = User
        fields = DjangoUserCreationForm.Meta.fields + ('email',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            
            UserProfile.objects.create(user=user)
        return user