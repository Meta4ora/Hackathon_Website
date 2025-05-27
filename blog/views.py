# views.py
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from django.db import connections, IntegrityError, DatabaseError, connection
from django.views.decorators.http import require_http_methods
from .forms import LoginForm, RegisterForm, ProfileForm, FeedbackForm, TeamRegistrationForm
from .models import PublicEvent
from django.contrib import messages
from django.utils.timezone import now
import logging
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

# Set up logging for debugging
logger = logging.getLogger(__name__)

def profile(request):
    if 'user_role' not in request.session or 'id' not in request.session:
        messages.error(request, "Пожалуйста, войдите в систему.")
        return redirect('login')

    user_data = {
        'email': request.session.get('email'),
        'user_role': request.session.get('user_role'),
        'id': request.session.get('id'),
    }

    # Fetch user details from the database
    with connections['org_db'].cursor() as cursor:
        if user_data['user_role'] == 'admin':
            cursor.execute("SELECT * FROM public.staff WHERE id_staff = %s", [user_data['id']])
        else:  # user_role == 'participant'
            cursor.execute("SELECT * FROM public.participants WHERE id_participant = %s", [user_data['id']])
        row = cursor.fetchone()
        if not row:
            logger.error(f"No user found for id: {user_data['id']} with role: {user_data['user_role']}")
            messages.error(request, "Пользователь не найден.")
            return redirect('custom_login')

        columns = [col[0] for col in cursor.description]
        user_details = dict(zip(columns, row))
        user_data.update(user_details)
        user_data['role'] = user_data['user_role']
        logger.debug(f"user_data after update: {user_data}")

    # Clean the phone number (remove trailing whitespace)
    if 'phone' in user_data:
        user_data['phone'] = user_data['phone'].strip()

    # Handle birth_date: Convert string to datetime.date if necessary
    birth_date = user_data.get('birth_date')
    if isinstance(birth_date, str):
        try:
            birth_date = datetime.strptime(birth_date, '%Y-%m-%d').date()
        except ValueError:
            logger.warning(f"Invalid birth_date format for user {user_data['id']}: {birth_date}")
            birth_date = None
    user_data['birth_date'] = birth_date

    # Debug: Log user_data to verify contents
    logger.debug(f"user_data: {user_data}")

    # Initialize forms
    initial_data = {
        'name': user_data.get('name', ''),
        'surname': user_data.get('surname', ''),
        'patronymic': user_data.get('patronymic', ''),
        'birth_date': user_data.get('birth_date').strftime('%Y-%m-%d') if user_data.get('birth_date') else None,
        'phone': user_data.get('phone', ''),
        'role': user_data.get('role', ''),  # Database role (e.g., 'Крутой')
    }
    profile_form = ProfileForm(initial=initial_data)
    feedback_form = FeedbackForm(id_participant=user_data['id'] if user_data['user_role'] == 'participant' else None)
    team_form = TeamRegistrationForm()
    logger.debug(f"Feedback form initialized for id_participant: {user_data['id'] if user_data['user_role'] == 'participant' else None}")

    if request.method == 'POST':
        if 'profile_submit' in request.POST:
            profile_form = ProfileForm(request.POST)
            if profile_form.is_valid():
                try:
                    cleaned_data = profile_form.cleaned_data
                    with connections['org_db'].cursor() as cursor:
                        if user_data['user_role'] == 'admin':
                            cursor.execute("""
                                UPDATE public.staff
                                SET name = %s, surname = %s, patronymic = %s, birth_date = %s, phone = %s, role = %s
                                WHERE id_staff = %s
                            """, [
                                cleaned_data['name'],
                                cleaned_data['surname'],
                                cleaned_data['patronymic'],
                                cleaned_data['birth_date'],
                                cleaned_data['phone'],
                                cleaned_data['role'],
                                user_data['id']
                            ])
                        else:  # user_role == 'participant'
                            cursor.execute("""
                                UPDATE public.participants
                                SET name = %s, surname = %s, patronymic = %s, birth_date = %s, phone = %s, role = %s
                                WHERE id_participant = %s
                            """, [
                                cleaned_data['name'],
                                cleaned_data['surname'],
                                cleaned_data['patronymic'],
                                cleaned_data['birth_date'],
                                cleaned_data['phone'],
                                cleaned_data['role'],
                                user_data['id']
                            ])
                    messages.success(request, "Данные профиля успешно обновлены!")
                    return redirect('profile')
                except (IntegrityError, DatabaseError) as e:
                    logger.error(f"Database error during profile update: {str(e)}")
                    messages.error(request, f"Ошибка при обновлении данных: {str(e)}")
            else:
                logger.debug(f"Profile form errors: {profile_form.errors}")
                messages.error(request, "Пожалуйста, исправьте ошибки в форме профиля.")

        elif 'feedback_submit' in request.POST and user_data['user_role'] == 'participant':
            feedback_form = FeedbackForm(request.POST, id_participant=user_data['id'])
            if feedback_form.is_valid():
                try:
                    cleaned_data = feedback_form.cleaned_data
                    with connections['org_db'].cursor() as cursor:
                        # Get the next id_feedback
                        cursor.execute("SELECT MAX(id_feedback) FROM public.feedback")
                        max_id = cursor.fetchone()[0] or 0
                        new_id = max_id + 1

                        # Insert feedback
                        cursor.execute("""
                            INSERT INTO public.feedback (id_feedback, id_participant, id_event, feedback_text, feedback_date)
                            VALUES (%s, %s, %s, %s, %s)
                        """, [
                            new_id,
                            user_data['id'],
                            cleaned_data['event'],
                            cleaned_data['feedback_text'],
                            now()
                        ])
                    messages.success(request, "Отзыв успешно добавлен!")
                    request.session['show_feedback_modal'] = True
                    return redirect('profile')
                except (IntegrityError, DatabaseError) as e:
                    logger.error(f"Database error during feedback submission: {str(e)}")
                    messages.error(request, f"Ошибка при добавлении отзыва: {str(e)}")
            else:
                logger.debug(f"Feedback form errors: {feedback_form.errors}")
                messages.error(request, "Пожалуйста, исправьте ошибки в форме отзыва.")

        elif 'team_submit' in request.POST and user_data['user_role'] == 'participant':
            team_form = TeamRegistrationForm(request.POST)
            if team_form.is_valid():
                try:
                    cleaned_data = team_form.cleaned_data
                    with connections['org_db'].cursor() as cursor:
                        # Get the next id_team
                        cursor.execute("SELECT MAX(id_team) FROM public.teams")
                        max_id = cursor.fetchone()[0] or 0
                        new_team_id = max_id + 1

                        # Insert the new team
                        captain_name = f"{user_data['surname']} {user_data['name']} {user_data['patronymic']}"
                        cursor.execute("""
                            INSERT INTO public.teams (id_team, status, team_name, captain)
                            VALUES (%s, %s, %s, %s)
                        """, [
                            new_team_id,
                            cleaned_data['status'],
                            cleaned_data['team_name'],
                            captain_name
                        ])

                        # Associate the team with the event
                        cursor.execute("""
                            INSERT INTO public.event_teams (id_team, id_event)
                            VALUES (%s, %s)
                        """, [
                            new_team_id,
                            cleaned_data['event']
                        ])

                        # Associate participants with the team
                        participant_ids = [p['id_participant'] for p in cleaned_data['participants']]
                        for participant_id in participant_ids:
                            cursor.execute("""
                                INSERT INTO public.team_participant (id_team, id_participant)
                                VALUES (%s, %s)
                            """, [
                                new_team_id,
                                participant_id
                            ])

                    messages.success(request, "Команда успешно зарегистрирована!")
                    request.session['show_team_modal'] = True
                    return redirect('profile')
                except (IntegrityError, DatabaseError) as e:
                    logger.error(f"Database error during team registration: {str(e)}")
                    messages.error(request, f"Ошибка при регистрации команды: {str(e)}")
            else:
                logger.debug(f"Team form errors: {team_form.errors}")
                messages.error(request, "Пожалуйста, исправьте ошибки в форме регистрации команды.")

    # Clear modal triggers after rendering
    show_feedback_modal = request.session.pop('show_feedback_modal', False)
    show_team_modal = request.session.pop('show_team_modal', False)

    return render(request, 'profile.html', {
        'profile_form': profile_form,
        'feedback_form': feedback_form,
        'team_form': team_form,
        'user_data': user_data,
        'show_feedback_modal': show_feedback_modal,
        'show_team_modal': show_team_modal
    })