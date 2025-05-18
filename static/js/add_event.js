function handleAddEvent() {
    const currentRole = window.CURRENT_USER_ROLE || "";
    if (currentRole === "admin") {
        const modal = new bootstrap.Modal(document.getElementById('addEventModal'));
        modal.show();
    } else {
        alert("Добавление мероприятия доступно только пользователю с ролью администратора.");
    }
}