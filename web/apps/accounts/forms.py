"""Forms for accounts app."""

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

User = get_user_model()


class LoginForm(AuthenticationForm):
    """Custom login form with Bootstrap styling."""

    username = forms.CharField(
        label="사용자명",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "사용자명"}),
    )
    password = forms.CharField(
        label="비밀번호",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "비밀번호"}),
    )


class RegisterForm(UserCreationForm):
    """User registration form."""

    email = forms.EmailField(
        label="이메일",
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "이메일"}),
    )

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        labels = {
            "username": "사용자명",
        }
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "사용자명"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "비밀번호"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "비밀번호 확인"}
        )
        self.fields["password1"].label = "비밀번호"
        self.fields["password2"].label = "비밀번호 확인"
