# Импорт необходимых модулей для работы с формами, валидацией, базой данных и логированием
from django import forms
from django.core.exceptions import ValidationError
import re
import bcrypt
from django.db import connections, connection
from django import forms
from django.db import connections
from datetime import date
import logging
from psycopg2 import DatabaseError

# Инициализация логгера для записи событий и ошибок
logger = logging.getLogger(__name__)

# Класс формы для регистрации нового участника
class RegisterForm(forms.Form):
    # Поле для ввода email
    email = forms.EmailField(
        label="Email",
        max_length=254,
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваш email'})
    )
    # Поле для ввода пароля
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Введите пароль'}),
        min_length=8
    )
    # Поле для подтверждения пароля
    confirm_password = forms.CharField(
        label="Подтвердите пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Подтвердите пароль'}),
        min_length=8
    )
    # Поле для ввода имени
    name = forms.CharField(
        label="Имя",
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваше имя'})
    )
    # Поле для ввода фамилии
    surname = forms.CharField(
        label="Фамилия",
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите вашу фамилию'})
    )
    # Поле для ввода отчества (необязательное)
    patronymic = forms.CharField(
        label="Отчество",
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваше отчество (опционально)'})
    )
    # Поле для ввода даты рождения
    birth_date = forms.DateField(
        label="Дата рождения",
        required=True,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    # Поле для ввода номера телефона
    phone = forms.CharField(
        label="Телефон",
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваш телефон'})
    )
    # Поле для ввода роли в команде
    role = forms.CharField(
        label="Роль в команде",
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите вашу роль'})
    )

    # Метод проверки уникальности email
    def clean_email(self):
        email = self.cleaned_data.get('email')
        with connections['org_db'].cursor() as cursor:
            # Проверяем, существует ли email в таблице participants
            cursor.execute("SELECT email FROM public.participants WHERE email = %s", [email])
            if cursor.fetchone():
                raise ValidationError("Этот email уже зарегистрирован.")
        return email

    # Метод проверки формата номера телефона
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        # Проверка с использованием регулярного выражения (например, +79991234567)
        if not re.match(r'^\+?[1-9]\d{1,14}$', phone):
            raise ValidationError("Введите корректный номер телефона (например, +79991234567).")
        return phone

    # Общая валидация формы
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        # Проверка совпадения пароля и подтверждения
        if password and confirm_password and password != confirm_password:
            raise ValidationError("Пароли не совпадают.")
        return cleaned_data

    # Метод сохранения нового участника в базе данных
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
            # Получаем максимальный id_participant для генерации нового ID
            cursor.execute("SELECT MAX(id_participant) FROM public.participants")
            last_id = cursor.fetchone()[0] or 0
            new_id = last_id + 1
            # Вызываем хранимую процедуру для создания участника
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
        # Возвращаем данные нового участника
        return {
            'id_participant': new_id,
            'email': email,
            'role': "Конкурсант"
        }

# Класс формы для аутентификации пользователя
class LoginForm(forms.Form):
    # Поле для ввода email
    email = forms.EmailField(label='Электронная почта')
    # Поле для ввода пароля
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

    # Метод аутентификации пользователя
    def authenticate_user(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        with connections['org_db'].cursor() as cursor:
            # Проверяем таблицу staff для администраторов
            cursor.execute("SELECT * FROM public.staff WHERE email = %s", [email])
            staff_row = cursor.fetchone()
            if staff_row:
                columns = [col[0] for col in cursor.description]
                staff = dict(zip(columns, staff_row))
                # Проверяем хеш пароля с использованием bcrypt
                if bcrypt.checkpw(password.encode('utf-8'), staff['password_hash'].encode('utf-8')):
                    return 'admin', staff
            # Проверяем таблицу participants для участников
            cursor.execute("SELECT * FROM public.participants WHERE email = %s", [email])
            participant_row = cursor.fetchone()
            if participant_row:
                columns = [col[0] for col in cursor.description]
                participant = dict(zip(columns, participant_row))
                if bcrypt.checkpw(password.encode('utf-8'), participant['password_hash'].encode('utf-8')):
                    return 'participant', participant
        # Вызываем ошибку при неверных учетных данных
        raise ValidationError("Неверный email или пароль")

# Импорты для формы редактирования профиля
from django import forms
from django.core.exceptions import ValidationError
import re
from datetime import date

# Класс формы для редактирования профиля пользователя
class ProfileForm(forms.Form):
    # Поле для имени
    name = forms.CharField(label="Имя", max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    # Поле для фамилии
    surname = forms.CharField(label="Фамилия", max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}))
    # Поле для отчества (необязательное)
    patronymic = forms.CharField(label="Отчество", max_length=50, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    # Поле для даты рождения
    birth_date = forms.DateField(
        label="Дата рождения",
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}, format='%Y-%m-%d'),
        required=False  # Поле необязательное
    )
    # Поле для номера телефона
    phone = forms.CharField(label="Телефон", max_length=15, widget=forms.TextInput(attrs={'class': 'form-control'}))
    # Поле для роли в команде
    role = forms.CharField(label="Роль в команде", max_length=15, widget=forms.TextInput(attrs={'class': 'form-control'}))

    # Метод проверки формата номера телефона
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^\+?[1-9]\d{1,14}$', phone):
            raise ValidationError("Введите корректный номер телефона (например, +79991234567).")
        return phone

    # Метод проверки даты рождения
    def clean_birth_date(self):
        birth_date = self.cleaned_data.get('birth_date')
        if birth_date and birth_date > date.today():
            raise ValidationError("Дата рождения не может быть в будущем.")
        return birth_date

# Повторная инициализация логгера
logger = logging.getLogger(__name__)

# Класс формы для отправки отзыва о мероприятии
class FeedbackForm(forms.Form):
    # Поле для выбора мероприятия
    event = forms.ChoiceField(
        label="Мероприятие",
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )
    # Поле для текста отзыва
    feedback_text = forms.CharField(
        label="Отзыв",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Введите ваш отзыв'}),
        max_length=1000,
        required=True
    )

    # Инициализация формы с динамическим списком мероприятий
    def __init__(self, *args, **kwargs):
        id_participant = kwargs.pop('id_participant', None)
        super().__init__(*args, **kwargs)
        logger.debug(f"Initializing FeedbackForm with id_participant: {id_participant}")
        if id_participant:
            try:
                with connections['org_db'].cursor() as cursor:
                    # Запрашиваем мероприятия, в которых участник зарегистрирован через команду
                    cursor.execute("""
                        SELECT DISTINCT e.id_event, e.event_name
                        FROM public.events e
                        JOIN public.event_teams te ON e.id_event = te.id_event
                        JOIN public.team_participant tp ON te.id_team = tp.id_team
                        WHERE tp.id_participant = %s
                        AND (e.end_date >= %s OR e.end_date IS NULL)
                        ORDER BY e.event_name
                    """, [id_participant, date.today()])
                    events = cursor.fetchall()
                    logger.debug(f"Events for id_participant {id_participant}: {events}")
                    # Заполняем список выбора мероприятий
                    self.fields['event'].choices = [(str(event[0]), event[1]) for event in events]
                    if not events:
                        logger.warning(f"No events found for id_participant {id_participant}")
                        self.fields['event'].choices = [('', 'Нет доступных мероприятий')]
            except DatabaseError as e:
                logger.error(f"Error fetching events for id_participant {id_participant}: {str(e)}")
                self.fields['event'].choices = [('', 'Ошибка загрузки мероприятий')]
        self.id_participant = id_participant  # Сохраняем ID участника для использования в clean

    # Проверка данных формы
    def clean(self):
        cleaned_data = super().clean()
        event_id = cleaned_data.get('event')
        feedback_text = cleaned_data.get('feedback_text')
        # Проверка заполнения обязательных полей
        if not event_id or not feedback_text:
            raise ValidationError("Все поля обязательны для заполнения.")
        if event_id == '':
            raise ValidationError("Выберите мероприятие.")
        # Проверка наличия существующего отзыва
        if self.id_participant and event_id:
            try:
                with connections['org_db'].cursor() as cursor:
                    cursor.execute("""
                        SELECT id_feedback
                        FROM public.feedback
                        WHERE id_participant = %s AND id_event = %s
                    """, [self.id_participant, event_id])
                    existing_feedback = cursor.fetchone()
                    if existing_feedback:
                        logger.warning(f"Feedback already exists for id_participant {self.id_participant} and id_event {event_id}")
                        raise ValidationError("Вы уже оставили отзыв на это мероприятие.")
            except DatabaseError as e:
                logger.error(f"Error checking existing feedback for id_participant {self.id_participant}, id_event {event_id}: {str(e)}")
                raise ValidationError("Ошибка при проверке отзыва. Попробуйте позже.")
        # Проверка регистрации участника на мероприятие
        if self.id_participant and event_id:
            try:
                with connections['org_db'].cursor() as cursor:
                    cursor.execute("""
                        SELECT 1
                        FROM public.events e
                        JOIN public.event_teams te ON e.id_event = te.id_event
                        JOIN public.team_participant tp ON te.id_team = tp.id_team
                        WHERE tp.id_participant = %s AND e.id_event = %s
                    """, [self.id_participant, event_id])
                    if not cursor.fetchone():
                        logger.warning(f"Participant {self.id_participant} is not registered for event {event_id}")
                        raise ValidationError("Вы не зарегистрированы на выбранное мероприятие.")
            except DatabaseError as e:
                logger.error(f"Error verifying event registration for id_participant {self.id_participant}, id_event {event_id}: {str(e)}")
                raise ValidationError("Ошибка при проверке регистрации на мероприятие.")
        return cleaned_data

# Повторная инициализация логгера
logger = logging.getLogger(__name__)

# Класс формы для регистрации новой команды
class TeamRegistrationForm(forms.Form):
    # Поле для названия команды
    team_name = forms.CharField(
        label="Название команды",
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'team_name'}),
        required=True
    )
    # Поле для выбора статуса команды
    status = forms.ChoiceField(
        label="Статус",
        choices=[('Активна', 'Активна'), ('Неактивна', 'Неактивна')],
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'status'}),
        required=True
    )
    # Скрытое поле для ID капитана
    captain_id = forms.IntegerField(
        widget=forms.HiddenInput(attrs={'id': 'captain_id'}),
        required=True
    )
    # Поле для выбора мероприятия
    event = forms.ChoiceField(
        label="Мероприятие",
        widget=forms.Select(attrs={'class': 'form-control', 'id': 'event'}),
        required=True
    )
    # Поле для выбора количества участников
    num_participants = forms.ChoiceField(
        label="Количество участников",
        choices=[(str(i), str(i)) for i in range(1, 6)],
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'num_participants'}),
        required=True
    )
    # Поля для данных дополнительных участников (до 4)
    player_1_surname = forms.CharField(
        label="Фамилия участника 1",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'player_1_surname'}),
        required=False
    )
    player_1_name = forms.CharField(
        label="Имя участника 1",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'player_1_name'}),
        required=False
    )
    player_1_patronymic = forms.CharField(
        label="Отчество участника 1",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'player_1_patronymic'}),
        required=False
    )
    player_1_email = forms.EmailField(
        label="Email участника 1",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'id': 'player_1_email'}),
        required=False
    )
    player_2_surname = forms.CharField(
        label="Фамилия участника 2",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'player_2_surname'}),
        required=False
    )
    player_2_name = forms.CharField(
        label="Имя участника 2",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'player_2_name'}),
        required=False
    )
    player_2_patronymic = forms.CharField(
        label="Отчество участника 2",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'player_2_patronymic'}),
        required=False
    )
    player_2_email = forms.EmailField(
        label="Email участника 2",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'id': 'player_2_email'}),
        required=False
    )
    player_3_surname = forms.CharField(
        label="Фамилия участника 3",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'player_3_surname'}),
        required=False
    )
    player_3_name = forms.CharField(
        label="Имя участника 3",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'player_3_name'}),
        required=False
    )
    player_3_patronymic = forms.CharField(
        label="Отчество участника 3",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'player_3_patronymic'}),
        required=False
    )
    player_3_email = forms.CharField(
        label="Email участника 3",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'id': 'player_3_email'}),
        required=False
    )
    player_4_surname = forms.CharField(
        label="Фамилия участника 4",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'player_4_surname'}),
        required=False
    )
    player_4_name = forms.CharField(
        label="Имя участника 4",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'player_4_name'}),
        required=False
    )
    player_4_patronymic = forms.CharField(
        label="Отчество участника 4",
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'player_4_patronymic'}),
        required=False
    )
    player_4_email = forms.EmailField(
        label="Email участника 4",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'id': 'player_4_email'}),
        required=False
    )

    # Инициализация формы с динамическим списком мероприятий
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            with connections['org_db'].cursor() as cursor:
                # Запрашиваем предстоящие мероприятия
                cursor.execute("""
                    SELECT id_event, event_name
                    FROM public.events
                    WHERE start_date >= %s
                    ORDER BY start_date
                """, [date.today()])
                events = cursor.fetchall()
                logger.debug(f"Upcoming events: {events}")
                # Заполняем список выбора мероприятий
                self.fields['event'].choices = [(str(event[0]), event[1]) for event in events]
                if not events:
                    logger.warning("No upcoming events found")
                    self.fields['event'].choices = [('', 'Нет доступных мероприятий')]
        except DatabaseError as e:
            logger.error(f"Error fetching events: {str(e)}")
            self.fields['event'].choices = [('', 'Ошибка загрузки мероприятий')]

    # Проверка данных формы
    def clean(self):
        cleaned_data = super().clean()
        team_name = cleaned_data.get('team_name')
        captain_id = cleaned_data.get('captain_id')
        event_id = cleaned_data.get('event')
        status = cleaned_data.get('status')
        num_participants = int(cleaned_data.get('num_participants', 1))
        # Проверка заполнения обязательных полей
        if not team_name or not captain_id or not event_id or not status:
            raise ValidationError("Все обязательные поля должны быть заполнены.")
        if event_id == '':
            raise ValidationError("Выберите мероприятие.")
        # Проверка уникальности названия команды
        try:
            with connections['org_db'].cursor() as cursor:
                cursor.execute("""
                    SELECT id_team
                    FROM public.teams
                    WHERE team_name = %s
                """, [team_name])
                if cursor.fetchone():
                    raise ValidationError("Команда с таким названием уже существует.")
        except DatabaseError as e:
            logger.error(f"Error checking team name uniqueness: {str(e)}")
            raise ValidationError("Ошибка при проверке названия команды.")
        # Проверка количества участников
        if num_participants < 1 or num_participants > 5:
            raise ValidationError("Количество участников должно быть от 1 до 5.")
        participants = []
        emails = set()
        captain_email = None
        # Получаем email капитана
        try:
            with connections['org_db'].cursor() as cursor:
                cursor.execute("""
                    SELECT email
                    FROM public.participants
                    WHERE id_participant = %s
                """, [captain_id])
                captain_email = cursor.fetchone()
                if captain_email:
                    captain_email = captain_email[0]
                    emails.add(captain_email)
        except DatabaseError as e:
            logger.error(f"Error fetching captain email: {str(e)}")
            raise ValidationError("Ошибка при проверке капитана.")
        # Проверка регистрации капитана на мероприятие
        try:
            with connections['org_db'].cursor() as cursor:
                cursor.execute("""
                    SELECT t.id_team
                    FROM public.teams t
                    JOIN public.event_teams et ON t.id_team = et.id_team
                    JOIN public.team_participant tp ON t.id_team = tp.id_team
                    WHERE tp.id_participant = %s AND et.id_event = %s
                """, [captain_id, event_id])
                if cursor.fetchone():
                    raise ValidationError("Вы уже зарегистрированы на это мероприятие в составе другой команды.")
        except DatabaseError as e:
            logger.error(f"Error checking captain's existing registration: {str(e)}")
            raise ValidationError("Ошибка при проверке регистрации капитана на мероприятие.")
        # Если количество участников равно 1, добавляем только капитана
        if num_participants == 1:
            participants.append({'id_participant': captain_id})
        else:
            # Проверяем данные дополнительных участников
            num_additional = num_participants - 1
            for i in range(1, num_additional + 1):
                surname = cleaned_data.get(f'player_{i}_surname')
                name = cleaned_data.get(f'player_{i}_name')
                patronymic = cleaned_data.get(f'player_{i}_patronymic', '')
                email = cleaned_data.get(f'player_{i}_email')
                # Проверка заполнения хотя бы одного поля
                fio_filled = any([surname, name, email])
                if not fio_filled:
                    raise ValidationError(f"Для участника {i} должны быть указаны фамилия, имя и email.")
                if not (surname and name and email):
                    raise ValidationError(f"Для участника {i} должны быть указаны все обязательные поля: фамилия, имя и email.")
                # Проверка уникальности email
                if email in emails:
                    raise ValidationError(f"Email участника {i} уже указан в другой карточке или совпадает с email капитана.")
                emails.add(email)
                # Поиск участника в базе данных
                try:
                    with connections['org_db'].cursor() as cursor:
                        cursor.execute("""
                            SELECT id_participant
                            FROM public.participants
                            WHERE surname = %s AND name = %s AND patronymic = %s AND email = %s
                        """, [surname, name, patronymic or '', email])
                        participant = cursor.fetchone()
                        if not participant:
                            raise ValidationError(f"Участник {i} ({surname} {name} {patronymic}, {email}) не найден в базе данных.")
                        participant_id = participant[0]
                        # Проверка регистрации участника на мероприятии
                        cursor.execute("""
                            SELECT t.id_team
                            FROM public.teams t
                            JOIN public.event_teams et ON t.id_team = et.id_team
                            JOIN public.team_participant tp ON t.id_team = tp.id_team
                            WHERE tp.id_participant = %s AND et.id_event = %s
                        """, [participant_id, event_id])
                        if cursor.fetchone():
                            raise ValidationError(f"Участник {i} ({surname} {name} {patronymic}, {email}) уже зарегистрирован на это мероприятие в составе другой команды.")
                        participants.append({'id_participant': participant_id})
                except DatabaseError as e:
                    logger.error(f"Error searching for participant {i}: {str(e)}")
                    raise ValidationError(f"Ошибка при поиске участника {i} в базе данных.")
            # Добавляем капитана в список участников
            participants.append({'id_participant': captain_id})
        cleaned_data['participants'] = participants
        return cleaned_data

# Класс формы для регистрации ментора
class MentorRegistrationForm(forms.Form):
    # Поле для фамилии
    surname = forms.CharField(max_length=50, required=True)
    # Поле для имени
    name = forms.CharField(max_length=50, required=True)
    # Поле для отчества (необязательное)
    patronymic = forms.CharField(max_length=50, required=False)
    # Поле для email
    email = forms.EmailField(required=True)
    # Поле для номера телефона
    phone = forms.CharField(max_length=15, required=True)
    # Поле для ID мероприятия
    event_id = forms.IntegerField(required=True)

    # Метод проверки формата номера телефона
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^\+?[1-9]\d{1,14}$', phone):
            raise ValidationError("Введите корректный номер телефона (например, +79991234567).")
        return phone

    # Метод проверки доступности мероприятия для регистрации ментора
    def clean_event_id(self):
        event_id = self.cleaned_data.get('event_id')
        with connection.cursor() as cursor:
            # Проверяем, что мероприятие существует, ещё не началось и не имеет ментора
            cursor.execute("""
                SELECT id_event FROM events
                WHERE id_event = %s AND start_date > CURRENT_DATE AND id_mentor IS NULL
            """, [event_id])
            if not cursor.fetchone():
                raise ValidationError("Выбранное мероприятие недоступно для регистрации ментора.")
        return event_id