from django.db import connections
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.core.exceptions import ValidationError

from .forms import LoginForm, RegisterForm
from .models import PublicEvent

def index(request):
    events = PublicEvent.objects.all().order_by('-start_date')[:6]
    # Проверяем, авторизован ли пользователь
    is_authenticated = 'user_role' in request.session and 'participant_id' in request.session
    user_data = {
        'email': request.session.get('participant_email'),
        'role': request.session.get('user_role'),
    } if is_authenticated else None
    return render(request, 'index.html', {
        'events': events,
        'is_authenticated': is_authenticated,
        'user_data': user_data,
    })

def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user_data = form.save()  # Сохраняем пользователя и получаем данные
            # Устанавливаем данные в сессию для авторизации
            request.session['user_role'] = user_data['role']
            request.session['participant_id'] = user_data['id_participant']
            request.session['participant_email'] = user_data['email']
            messages.success(request, "Регистрация прошла успешно! Вы вошли в систему.")
            return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

def custom_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            try:
                role, user_data = form.authenticate_user()
                request.session['user_role'] = role
                request.session['participant_id'] = user_data['id_participant']
                request.session['participant_email'] = user_data['email']
                return redirect('index')
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = LoginForm()
    return render(request, 'authorization.html', {'form': form})

def profile(request):
    if 'user_role' in request.session and 'participant_id' in request.session:
        user_data = {
            'email': request.session.get('participant_email'),
            'role': request.session.get('user_role'),
            'participant_id': request.session.get('participant_id'),
        }
        print("user_data", user_data)
        with connections['org_db'].cursor() as cursor:
            cursor.execute("SELECT * FROM public.participants WHERE id_participant = %s", [user_data['participant_id']])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                participant = dict(zip(columns, row))
                user_data.update(participant)
        return render(request, 'profile.html', {'user_data': user_data})
    else:
        return redirect('login')

def custom_logout(request):
    request.session.flush()
    return redirect('index')