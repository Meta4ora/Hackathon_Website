// Ожидаем полной загрузки DOM перед выполнением скрипта
document.addEventListener("DOMContentLoaded", () => {
    // Получаем все карточки обратной связи
    const feedbackCards = document.querySelectorAll('.feedback-card');
    // Получаем кнопку "Загрузить ещё"
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    // Количество карточек для начального отображения
    const initialBatch = 8;
    // Количество карточек для отображения при нажатии на кнопку
    const batchSize = 4;
    // Счётчик показанных карточек
    let shown = 0;

    // Функция для отображения следующей партии карточек
    function showNextBatch(size) {
        let delay = 0; // Начальная задержка для анимации
        // Показываем карточки из текущей партии
        for (let i = shown; i < shown + size && i < feedbackCards.length; i++) {
            const card = feedbackCards[i];
            // Асинхронно показываем карточку с задержкой
            setTimeout(() => {
                card.style.display = 'block'; // Делаем карточку видимой
                // Используем requestAnimationFrame для плавного добавления класса анимации
                requestAnimationFrame(() => {
                    card.classList.add('visible'); // Добавляем класс для анимации видимости
                });
            }, delay);
            delay += 100; // Увеличиваем задержку для следующей карточки (100 мс)
        }
        // Обновляем счётчик показанных карточек
        shown += size;

        // Если все карточки показаны, скрываем кнопку "Загрузить ещё"
        if (shown >= feedbackCards.length && loadMoreBtn) {
            loadMoreBtn.classList.add('fade-out'); // Добавляем класс для анимации исчезновения
            // Скрываем кнопку после завершения анимации (500 мс)
            setTimeout(() => loadMoreBtn.style.display = 'none', 500);
        }
    }

    // Показываем начальную партию карточек при загрузке страницы
    showNextBatch(initialBatch);

    // Если кнопка "Загрузить ещё" существует, добавляем обработчик клика
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', () => showNextBatch(batchSize));
    }
});