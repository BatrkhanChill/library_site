# main/forms.py
import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import password_validation
from django.utils.translation import gettext_lazy as _
from .models import Profile, Student


def _validate_password_strength(password):
    """Минимум 8 символов, только латиница, хотя бы одна цифра и спецсимвол."""
    if len(password) < 8:
        raise forms.ValidationError(_('Пароль должен содержать не менее 8 символов.'))
    if not re.search(r'[A-Za-z]', password):
        raise forms.ValidationError(_('Пароль должен содержать латинские буквы.'))
    if re.search(r'[^A-Za-z0-9!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~]', password):
        raise forms.ValidationError(_('Пароль должен содержать только латинские буквы, цифры и спецсимволы.'))
    if not re.search(r'\d', password):
        raise forms.ValidationError(_('Пароль должен содержать хотя бы одну цифру.'))
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?`~]', password):
        raise forms.ValidationError(_('Пароль должен содержать хотя бы один спецсимвол (!@#$%^&* и т.д.).'))

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label=_('Email'))
    student_id = forms.CharField(required=True, label=_('ID'))

    class Meta:
        model = User
        fields = ['username', 'email', 'student_id', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields['student_id'].widget.attrs.update({'placeholder': '0001', 'maxlength': '4'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Пользователь с таким email уже существует.'))
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if password:
            _validate_password_strength(password)
        return password

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if not student_id:
            raise forms.ValidationError(_('Пожалуйста, укажите ID.'))
        try:
            student_id = Student.normalize_student_id(student_id)
        except Exception as exc:
            raise forms.ValidationError(exc)
        if not Student.objects.filter(student_id=student_id).exists():
            raise forms.ValidationError(_('ID не найден в базе. Обратитесь к администрации.'))
        if Profile.objects.filter(student_id=student_id).exists():
            raise forms.ValidationError(_('Пользователь с таким ID уже зарегистрирован.'))
        return student_id

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.is_active = False
        student_id = self.cleaned_data.get('student_id')
        student = Student.objects.filter(student_id=student_id).first()
        if student:
            full_name = (student.full_name or '').strip().split()
            if full_name:
                user.last_name = full_name[0]
                if len(full_name) > 1:
                    user.first_name = full_name[1]
        if commit:
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.student_id = student_id
            if student:
                profile.group_name = student.group_name or profile.group_name
            profile.save()
            profile.sync_with_student_data()
        return user

class VerificationCodeForm(forms.Form):
    code = forms.CharField(max_length=6, label=_('Код подтверждения'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['code'].widget.attrs.update({
            'class': 'form-control form-control-lg',
            'placeholder': '000000',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
        })

    def clean_code(self):
        code = (self.cleaned_data.get('code') or '').strip()
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError(_('Введите корректный 6-значный код.'))
        return code


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label=_('Email'))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control form-control-lg'})


class SetPasswordByCodeForm(VerificationCodeForm):
    new_password1 = forms.CharField(widget=forms.PasswordInput, label=_('Новый пароль'))
    new_password2 = forms.CharField(widget=forms.PasswordInput, label=_('Подтвердите новый пароль'))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        for field in ('new_password1', 'new_password2'):
            self.fields[field].widget.attrs.update({'class': 'form-control form-control-lg'})

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('new_password1')
        password2 = cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_('Пароли не совпадают.'))
        if password1:
            password_validation.validate_password(password1, self.user)
        return cleaned_data


class UserEditForm(forms.ModelForm):
    """
    Форма для редактирования данных пользователя
    """
    first_name = forms.CharField(max_length=150, required=False, label=_('Имя'))
    last_name = forms.CharField(max_length=150, required=False, label=_('Фамилия'))
    email = forms.EmailField(required=True, label=_('Email'))
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

class ProfileEditForm(forms.ModelForm):
    """
    Форма для редактирования профиля пользователя
    """
    class Meta:
        model = Profile
        fields = [
            'phone', 'address', 'birth_date', 'student_id', 
            'group_name', 'bio', 'telegram', 'instagram', 'avatar'
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+7 (XXX) XXX-XX-XX'}),
            'student_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '0001', 'maxlength': '4'}),
            'group_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: ИС-21'}),
            'telegram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}),
            'instagram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}),
        }
        labels = {
            'phone': _('Телефон'),
            'address': _('Адрес'),
            'birth_date': _('Дата рождения'),
            'student_id': _('ID'),
            'group_name': _('Группа'),
            'bio': _('О себе'),
            'telegram': _('Telegram'),
            'instagram': _('Instagram'),
            'avatar': _('Фото профиля'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'avatar':
                self.fields[field].widget.attrs.update({'class': 'form-control'})

        if self.instance and self.instance.student_id:
            self.fields['student_id'].disabled = True

    def clean_student_id(self):
        student_id = self.cleaned_data.get('student_id')
        if not student_id:
            return student_id
        try:
            return Student.normalize_student_id(student_id)
        except Exception as exc:
            raise forms.ValidationError(exc)