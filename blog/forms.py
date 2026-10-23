from django import forms
from .models import Post
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]


class PostForm(forms.ModelForm):
    image_fields = ("cover_image", "image_2", "image_3")

    class Meta:
        model = Post
        fields = [
            "title",
            "content",
            "category",
            "tags",
            "status",
            "cover_image",
            "image_2",
            "image_3",
        ]

        widgets = {
            "content": forms.Textarea(attrs={"rows": 8, "class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

        labels = {
            "cover_image": "Photo 1 (cover)",
            "image_2": "Photo 2",
            "image_3": "Photo 3",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.image_fields:
            self.fields[field_name].required = not bool(
                getattr(self.instance, field_name)
            )

    def clean_title(self):
        title = self.cleaned_data["title"]
        if len(title) < 5:
            raise forms.ValidationError("Title must be at least 5 characters long.")
        return title

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get("title")
        content = cleaned_data.get("content")
        if title and content and title.lower()[:50] in content.lower()[:50]:
            raise forms.ValidationError(
                "Don't repeat the title verbatim at the start of the content."
            )
        if any(not cleaned_data.get(field_name) for field_name in self.image_fields):
            raise forms.ValidationError("Please upload all 3 post photos.")
        return cleaned_data

    def _clean_image(self, field_name):
        image = self.cleaned_data.get(field_name)
        if image:
            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError("Image file too large (max 5MB).")

            valid_extensions = [".jpg", ".jpeg", ".png", ".webp"]
            if not any(image.name.lower().endswith(ext) for ext in valid_extensions):
                raise forms.ValidationError("Unsupported file type. Use JPG, PNG, or WEBP.")

        return image

    def clean_cover_image(self):
        return self._clean_image("cover_image")

    def clean_image_2(self):
        return self._clean_image("image_2")

    def clean_image_3(self):
        return self._clean_image("image_3")