# views.py
from django.db import connections
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError

from .forms import LoginForm, RegisterForm
from .models import PublicEvent

def index(request):
    events = PublicEvent.objects.all().order_by('-start_date')[:6]
    # Проверяем, авторизован ли пользователь
    is_authenticated = 'user_role' in request.session and 'id' in request.session
    user_data = {
        'email': request.session.get('email'),
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
            request.session['id'] = user_data['id_participant']
            request.session['email'] = user_data['email']
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
                # Set the ID based on the role
                if role == 'admin':
                    request.session['id'] = user_data['id_staff']  # Adjust 'id_staff' to match your staff table's primary key column
                else:  # role == 'participant'
                    request.session['id'] = user_data['id_participant']
                request.session['email'] = user_data['email']
                return redirect('index')
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = LoginForm()
    return render(request, 'authorization.html', {'form': form})

def profile(request):
    if 'user_role' in request.session and 'id' in request.session:
        user_data = {
            'email': request.session.get('email'),
            'role': request.session.get('user_role'),
            'id': request.session.get('id'),
        }
        with connections['org_db'].cursor() as cursor:
            if user_data['role'] == 'admin':
                cursor.execute("SELECT * FROM public.staff WHERE id_staff = %s", [user_data['id']])
            else:  # role == 'participant'
                cursor.execute("SELECT * FROM public.participants WHERE id_participant = %s", [user_data['id']])
            row = cursor.fetchone()
            if row:
                columns = [col[0] for col in cursor.description]
                user_details = dict(zip(columns, row))
                user_data.update(user_details)
        return render(request, 'profile.html', {'user_data': user_data})
    else:
        return redirect('login')

def custom_logout(request):
    request.session.flush()
    return redirect('index')

def events(request):
    events = PublicEvent.objects.all().order_by('-start_date')
    is_authenticated = 'user_role' in request.session and 'id' in request.session
    user_data = {
        'email': request.session.get('email'),
        'role': request.session.get('user_role'),
    } if is_authenticated else None
    return render(request, 'events.html', {
        'events': events,
        'is_authenticated': is_authenticated,
        'user_data': user_data,
    })

def event_detail(request, event_id):
    event = get_object_or_404(PublicEvent, id_event=event_id)
    is_authenticated = 'user_role' in request.session and 'id' in request.session
    user_data = {
        'email': request.session.get('email'),
        'role': request.session.get('user_role'),
    } if is_authenticated else None
    return render(request, 'event_detail.html', {
        'event': event,
        'is_authenticated': is_authenticated,
        'user_data': user_data,
    })
