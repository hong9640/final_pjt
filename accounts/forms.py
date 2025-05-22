from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label="이메일",
        error_messages={
            'required': '이메일을 입력해주세요.',
            'invalid': '올바른 이메일 주소를 입력해주세요.',
        },
        widget=forms.EmailInput(attrs={"placeholder": "example@email.com"})
    )

    password1 = forms.CharField(
        label="비밀번호",
        strip=False,
        widget=forms.PasswordInput,
        error_messages={
            'required': '비밀번호를 입력해주세요.',
        }
    )

    password2 = forms.CharField(
        label="비밀번호 확인",
        strip=False,
        widget=forms.PasswordInput,
        error_messages={
            'required': '비밀번호 확인을 입력해주세요.',
        }
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        labels = {
            "username": "아이디",
        }
        error_messages = {
            "username": {
                "required": "아이디를 입력해주세요.",
                "unique": "이미 사용 중인 아이디입니다.",
            }
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("이미 등록된 이메일입니다.")
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        try:
            validate_password(password1)
        except ValidationError as e:
            raise forms.ValidationError([
                self._translate_error(msg) for msg in e.messages
            ])
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("비밀번호가 일치하지 않습니다.")
        return password2

    def clean(self):
        cleaned_data = super().clean()
        # 여긴 그대로 둬도 괜찮음, 오류는 위에서 처리
        return cleaned_data

    def _translate_error(self, msg):
        translations = {
            "This password is too short. It must contain at least 8 characters.": "비밀번호는 최소 8자 이상이어야 합니다.",
            "This password is too common.": "너무 흔한 비밀번호입니다.",
            "This password is entirely numeric.": "비밀번호에 숫자 외의 문자를 포함시켜주세요.",
            "The two password fields didn’t match.": "비밀번호가 일치하지 않습니다.",
        }
        return translations.get(msg, msg)

class NoLabelClearableFileInput(forms.ClearableFileInput):
    template_name = 'widgets/only_input_file_widget.html'  # 별도 템플릿 사용

class CustomUserChangeForm(forms.ModelForm):
    profile_image = forms.ImageField(
        required=False,
        widget=NoLabelClearableFileInput(attrs={
            'class': 'form-input'
        })
    )

    class Meta:
        model = User
        fields = ('nickname', 'profile_image', 'email')
        widgets = {
            'nickname': forms.TextInput(attrs={'placeholder': '닉네임'}),
            'email': forms.EmailInput(attrs={'placeholder': '이메일'}),
        }