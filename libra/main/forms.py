# main/forms.py
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from .models import Profile

class UserEditForm(forms.ModelForm):
    """
    Форма для редактирования данных пользователя
    """
    first_name = forms.CharField(max_length=150, required=False, label="Имя")
    last_name = forms.CharField(max_length=150, required=False, label="Фамилия")
    email = forms.EmailField(required=True, label="Email")
    
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
            'student_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '№ студенческого билета'}),
            'group_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: ИС-21'}),
            'telegram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}),
            'instagram': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '@username'}),
        }
        labels = {
            'phone': 'Телефон',
            'address': 'Адрес',
            'birth_date': 'Дата рождения',
            'student_id': 'Номер студенческого билета',
            'group_name': 'Группа',
            'bio': 'О себе',
            'telegram': 'Telegram',
            'instagram': 'Instagram',
            'avatar': 'Фото профиля',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field != 'avatar':
                self.fields[field].widget.attrs.update({'class': 'form-control'})