document.addEventListener('DOMContentLoaded', function () {
    // ===========================
    // 1. Модальные окна (успехи)
    // ===========================
    const body = document.body;
    const showFeedbackModal = body.dataset.showFeedback === 'true';
    const showTeamModal = body.dataset.showTeam === 'true';

    if (showFeedbackModal) {
        const feedbackModal = document.getElementById('feedbackSuccessModal');
        if (feedbackModal) {
            new bootstrap.Modal(feedbackModal).show();
        }
    }

    if (showTeamModal) {
        const teamModal = document.getElementById('teamSuccessModal');
        if (teamModal) {
            new bootstrap.Modal(teamModal).show();
        }
    }

    // ========================================
    // 2. Динамическое отображение участников
    // ========================================
    const selectElement = document.getElementById('num_participants');
    if (!selectElement) {
        console.error('Element with id "num_participants" not found');
        return;
    }

    selectElement.addEventListener('change', function () {
        const numParticipants = parseInt(this.value);
        const totalCards = 4; // Максимум дополнительных участников (2–5)

        // Сначала скрываем все карточки
        for (let i = 1; i <= totalCards; i++) {
            const card = document.getElementById(`participant-card-${i}`);
            if (card) {
                card.style.display = 'none';
                card.querySelectorAll('input').forEach(input => input.value = '');
            }
        }

        // Показываем нужное количество карточек (без капитана)
        if (numParticipants > 1) {
            const cardsToShow = numParticipants - 1;
            for (let i = 1; i <= cardsToShow; i++) {
                const card = document.getElementById(`participant-card-${i}`);
                if (card) {
                    card.style.display = 'block';
                }
            }
        }
    });

    // Триггерим изменение при загрузке страницы, если уже выбрано значение
    selectElement.dispatchEvent(new Event('change'));
});
