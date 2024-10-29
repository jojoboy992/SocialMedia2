from django import forms
from .models import *
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
import re
from django.core.exceptions import ValidationError
from django.forms.widgets import ClearableFileInput
from PIL import Image
import moviepy.editor as mp
from io import BytesIO
import cv2
import tempfile
import logging

logging.basicConfig(level=logging.DEBUG)

# Custom Login Form
class CustomLoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(_("This account is inactive."))

        if not self.cleaned_data.get("password"):
            raise forms.ValidationError(_("Please enter your password."))


class CustomSignupForm(UserCreationForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(
        label="Confirm Password", widget=forms.PasswordInput
    )  # Change label here

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if len(username) > 15:
            raise forms.ValidationError("Username must not exceed 15 characters.")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already in use.")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise forms.ValidationError("Enter a valid email address.")
        return email

    def clean_password1(self):
        password = self.cleaned_data.get("password1")
        if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
            raise forms.ValidationError(
                "Password must contain at least one letter and one number."
            )
        return password



class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ["title", "image", "video"]
        labels = {"title": "Caption"}

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            img = Image.open(image)
            width, height = img.size
            if (width, height) < (1080, 1080):
                raise ValidationError(f"Image resolution must be at least 1080 x 1350 pixels. Current resolution: {width} x {height}.")
        return image

    def clean_video(self):
        video = self.cleaned_data.get('video')
        if video:
            try:
                # Temporarily save video for OpenCV processing
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as temp_video:
                    for chunk in video.chunks():
                        temp_video.write(chunk)
                    temp_video.seek(0)

                    # Log temp video path
                    logging.debug(f"Temporary video file created at: {temp_video.name}")

                    # Use OpenCV to check resolution
                    cap = cv2.VideoCapture(temp_video.name)
                    if not cap.isOpened():
                        raise ValidationError("Unable to open video file. Please ensure it's a valid video format.")
                    
                    # Get the width and height of the video
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    cap.release()  # Release the video after reading

                    # Log the obtained width and height
                    logging.debug(f"Video width: {width}, height: {height}")

                    # Check if resolution meets requirements
                    if (width, height) < (1080, 1080):
                        raise ValidationError(f"Video resolution must be at least 1080 x 1350 pixels. Current resolution: {width} x {height}.")
            except ValidationError as ve:
                raise ve  # Re-raise any validation errors to be handled by the form
            except Exception as e:
                logging.error(f"Error processing video: {e}")
                raise ValidationError("Unable to process video file. Please ensure it's a valid video format.")
        return video


class CustomClearableFileInput(ClearableFileInput):
    template_name = "widgets/custom_clearable_file_input.html"

    def use_required_attribute(self, initial):
        return False

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "title-input"})
        }


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["bio", "location", "birth_date", "profile_picture"]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "profile_picture": CustomClearableFileInput(),
        }

    # Add validation for the bio field
    def clean_bio(self):
        bio = self.cleaned_data.get("bio")
        if len(bio) > 150:
            raise ValidationError("Bio cannot be longer than 150 characters.")
        return bio


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]  # Only the content field is needed
        widgets = {
            "content": forms.TextInput(attrs={"placeholder": "Enter your comment..."}),
        }


class ReplyForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["content"]  # Only the content field is needed for replies
        widgets = {
            "content": forms.TextInput(attrs={"placeholder": "Enter your reply..."}),
        }


class UserSearchForm(forms.Form):
    query = forms.CharField(label="Search Users", max_length=100)
