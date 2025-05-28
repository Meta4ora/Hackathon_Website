// Ожидаем полной загрузки DOM перед выполнением скрипта
document.addEventListener('DOMContentLoaded', function () {
    // Кэшируем document.body для эффективного доступа
    const body = document.body;

    // Проверяем, нужно ли показать модальное окно обратной связи на основе атрибута dataset
    const showFeedbackModal = body.dataset.showFeedback === 'true';
    // Проверяем, нужно ли показать модальное окно команды на основе атрибута dataset
    const showTeamModal = body.dataset.showTeam === 'true';

    // Отображаем модальное окно обратной связи, если showFeedbackModal равно true
    if (showFeedbackModal) {
        const feedbackModal = document.getElementById('feedbackSuccessModal');
        if (feedbackModal) {
            // Инициализируем и показываем модальное окно Bootstrap для обратной связи
            new bootstrap.Modal(feedbackModal).show();
        }
    }

    // Отображаем модальное окно команды, если showTeamModal равно true
    if (showTeamModal) {
        const teamModal = document.getElementById('teamSuccessModal');
        if (teamModal) {
            // Инициализируем и показываем модальное окно Bootstrap для команды
            new bootstrap.Modal(teamModal).show();
        }
    }

    // Получаем элемент select для выбора количества участников
    const selectElement = document.getElementById('num_participants');
    // Проверяем, существует ли элемент select, и выводим ошибку, если не найден
    if (!selectElement) {
        console.error('Элемент с id "num_participants" не найден');
        return; // Прерываем выполнение функции
    }

    // Добавляем обработчик события для изменения количества участников
    selectElement.addEventListener('change', function () {
        // Преобразуем выбранное значение в целое число
        const numParticipants = parseInt(this.value);
        // Определяем максимальное количество дополнительных карточек участников (2–5)
        const totalCards = 4;

        // Скрываем все карточки участников и очищаем их поля ввода
        for (let i = 1; i <= totalCards; i++) {
            const card = document.getElementById(`participant-card-${i}`);
            if (card) {
                card.style.display = 'none'; // Скрываем карточку
                // Очищаем все поля ввода в карточке
                card.querySelectorAll('input').forEach(input => input.value = '');
            }
        }

        // Показываем нужное количество карточек участников (без капитана)
        if (numParticipants > 1) {
            const cardsToShow = numParticipants - 1; // Количество дополнительных участников
            for (let i = 1; i <= cardsToShow; i++) {
                const card = document.getElementById(`participant-card-${i}`);
                if (card) {
                    card.style.display = 'block'; // Показываем карточку
                }
            }
        }
    });

    // Запускаем событие 'change' при загрузке страницы для инициализации карточек
    selectElement.dispatchEvent(new Event('change'));
});