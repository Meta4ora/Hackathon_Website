# views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from django.db import connections, IntegrityError, DatabaseError, connection
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.shortcuts import redirect, render
from .forms import LoginForm, RegisterForm
from .models import PublicEvent
from django.utils.timezone import now

def index(request):
    events = PublicEvent.objects.all().order_by('-start_date')[:6]
    is_authenticated = 'user_role' in request.session and 'id' in request.session
    user_data = {
        'email': request.session.get('email'),
        'role': request.session.get('user_role'),
    } if is_authenticated else None

    # Получаем отзывы
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT fb.feedback_text, fb.feedback_date, ev.event_name,
                   p.name, p.surname
            FROM feedback fb
            JOIN participants p ON fb.id_participant = p.id_participant
            JOIN eventdetailsview ev ON fb.id_event = ev.id_event
            ORDER BY fb.feedback_date DESC
            LIMIT 20
        """)
        raw_feedback = cursor.fetchall()
        feedback_list = [
            {
                'text': row[0],
                'date': row[1],
                'event_name': row[2],
                'first_name': row[3],
                'last_name': row[4],
            } for row in raw_feedback
        ]

    return render(request, 'index.html', {
        'events': events,
        'is_authenticated': is_authenticated,
        'user_data': user_data,
        'feedback_list': feedback_list,
        'now': now()
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
        'now': now()
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
        'now': now()
    })

@require_http_methods(["POST"])
def add_event(request):
    event_name = request.POST.get('event_name')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    id_venue = request.POST.get('id_venue')
    id_mentor = request.POST.get('id_mentor')

    try:
        with connections['default'].cursor() as cursor:
            # Получаем последний id_event
            cursor.execute("SELECT MAX(id_event) FROM public.events")
            max_id = cursor.fetchone()[0] or 0
            new_id = max_id + 1

            # Вставляем новое мероприятие
            cursor.execute("""
                INSERT INTO public.events (id_event, event_name, start_date, end_date, id_venue, id_mentor)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, [new_id, event_name, start_date, end_date, id_venue, id_mentor])

        messages.success(request, f"Мероприятие успешно добавлено с ID {new_id}.")

    except (IntegrityError, DatabaseError) as e:
        messages.error(request, f"Ошибка при добавлении мероприятия: {str(e)}")

    return redirect('events')
