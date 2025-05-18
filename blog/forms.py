# forms.py
from django import forms
from django.core.exceptions import ValidationError
import re
import bcrypt
from django.db import connections

class RegisterForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваш email'})
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'}),
        min_length=8
    )
    confirm_password = forms.CharField(
        label="Подтвердите пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Подтвердите пароль'}),
        min_length=8
    )
    name = forms.CharField(
        label="Имя",
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваше имя'})
    )
    surname = forms.CharField(
        label="Фамилия",
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите вашу фамилию'})
    )
    patronymic = forms.CharField(
        label="Отчество",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваше отчество (опционально)'})
    )
    birth_date = forms.DateField(
        label="Дата рождения",
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    phone = forms.CharField(
        label="Телефон",
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваш телефон'})
    )
    role = forms.CharField(
        label="Роль в команде",
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите вашу роль'})
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        with connections['org_db'].cursor() as cursor:
            cursor.execute("SELECT email FROM public.participants WHERE email = %s", [email])
            if cursor.fetchone():
                raise ValidationError("Этот email уже зарегистрирован.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Простая проверка формата телефона (например, +79991234567)
        if not re.match(r'^\+?[1-9]\d{1,14}$', phone):
            raise ValidationError("Введите корректный номер телефона (например, +79991234567).")
        return phone

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise ValidationError("Пароли не совпадают.")
        return cleaned_data

    def save(self):
        cleaned_data = self.cleaned_data
        email = cleaned_data['email']
        password = cleaned_data['password']
        name = cleaned_data['name']
        surname = cleaned_data['surname']
        patronymic = cleaned_data.get('patronymic', '')
        birth_date = cleaned_data['birth_date']
        phone = cleaned_data['phone']
        role = cleaned_data['role']

        with connections['org_db'].cursor() as cursor:
            # Получаем последний id_participant
            cursor.execute("SELECT MAX(id_participant) FROM public.participants")
            last_id = cursor.fetchone()[0] or 0
            new_id = last_id + 1

            # Вызываем процедуру для вставки нового участника
            cursor.execute("""
                CALL public.create_participant(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, [
                new_id,
                surname,
                name,
                patronymic,
                role,
                birth_date,
                email,
                phone,
                password
            ])

        return {
            'id_participant': new_id,
            'email': email,
            'role': "Конкурсант"
        }

class LoginForm(forms.Form):
    email = forms.EmailField(label='Электронная почта')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

    def authenticate_user(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        with connections['org_db'].cursor() as cursor:
            # First, check the staff table
            cursor.execute("SELECT * FROM public.staff WHERE email = %s", [email])
            staff_row = cursor.fetchone()
            if staff_row:
                columns = [col[0] for col in cursor.description]
                staff = dict(zip(columns, staff_row))
                # Assuming the password in the staff table is also hashed with bcrypt
                if bcrypt.checkpw(password.encode('utf-8'), staff['password_hash'].encode('utf-8')):
                    return 'admin', staff

            # If no match in staff, check the participants table
            cursor.execute("SELECT * FROM public.participants WHERE email = %s", [email])
            participant_row = cursor.fetchone()
            if participant_row:
                columns = [col[0] for col in cursor.description]
                participant = dict(zip(columns, participant_row))
                if bcrypt.checkpw(password.encode('utf-8'), participant['password_hash'].encode('utf-8')):
                    return 'participant', participant

        # If no match is found in either table
        raise ValidationError("Неверный email или пароль")