// Ожидаем полной загрузки DOM перед выполнением скрипта
document.addEventListener('DOMContentLoaded', function() {
    // Проверяем, определена ли переменная showFeedbackModal и равно ли её значение true (передаётся из шаблона Django)
    if (typeof showFeedbackModal !== 'undefined' && showFeedbackModal) {
        // Инициализируем модальное окно Bootstrap для обратной связи
        var feedbackModal = new bootstrap.Modal(document.getElementById('feedbackSuccessModal'));
        // Показываем модальное окно
        feedbackModal.show();
    }
});