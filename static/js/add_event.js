// Функция для обработки добавления мероприятия
function handleAddEvent() {
    // Получаем текущую роль пользователя из глобальной переменной, если она не определена — устанавливаем пустую строку
    const currentRole = window.CURRENT_USER_ROLE || "";
    // Проверяем, является ли пользователь администратором
    if (currentRole === "admin") {
        // Инициализируем модальное окно Bootstrap для добавления мероприятия
        const modal = new bootstrap.Modal(document.getElementById('addEventModal'));
        // Показываем модальное окно
        modal.show();
    } else {
        // Показываем предупреждение, если пользователь не имеет прав администратора
        alert("Добавление мероприятия доступно только пользователю с ролью администратора.");
    }
}