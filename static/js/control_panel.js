// Ожидаем полной загрузки DOM перед выполнением скрипта
    document.addEventListener('DOMContentLoaded', () => {
        // Получаем или создаём контейнер для сообщений
        const messagesContainer = document.getElementById('messages-container') || document.createElement('div');
        // Если контейнер не существует, задаём ему ID и класс, добавляем в начало элемента .card
        if (!messagesContainer.id) {
            messagesContainer.id = 'messages-container';
            messagesContainer.className = 'mb-3';
            document.querySelector('.card').prepend(messagesContainer);
        }

        // Функция для отображения временного сообщения (уведомления)
        function showMessage(message, type = 'danger') {
            const alert = document.createElement('div');
            alert.className = `alert alert-${type}`; // Задаём класс для стилизации (например, alert-danger)
            alert.textContent = message; // Устанавливаем текст сообщения
            messagesContainer.appendChild(alert); // Добавляем в контейнер
            setTimeout(() => alert.remove(), 5000); // Удаляем через 5 секунд
        }

        // Функция для отображения данных сводки в модальном окне
        function displaySummaryData(data) {
            console.log('Displaying summary data:', data);
            const modalBody = document.getElementById('summaryModalBody');
            let html = '<div class="table-responsive">'; // Обёртываем таблицу для прокрутки
            if (data && data.length > 0) {
                // Создаём таблицу, если есть данные
                html += '<table class="table table-striped"><thead><tr>';
                Object.keys(data[0]).forEach(key => {
                    html += `<th>${key}</th>`; // Добавляем заголовки столбцов
                });
                html += '</tr></thead><tbody>';
                data.forEach(row => {
                    // Добавляем строки таблицы
                    html += `<tr>${Object.values(row).map(value => `<td>${value ?? ''}</td>`).join('')}</tr>`;
                });
                html += '</tbody></table>';
            } else {
                html = '<p>Нет данных для отображения.</p>'; // Сообщение, если данных нет
            }
            html += '</div>';
            modalBody.innerHTML = html; // Вставляем HTML в тело модального окна
            // Показываем модальное окно
            new bootstrap.Modal(document.getElementById('summarySuccessModal')).show();
        }

        // Асинхронная функция для загрузки списка представлений и таблиц
        async function loadViews() {
            try {
                // Запрашиваем список представлений
                const response = await fetch('/api/get_views/', {
                    headers: { 'X-CSRFToken': getCookie('csrftoken') }
                });
                const views = await response.json();
                console.log('Loaded views:', views);
                const viewSelect = document.getElementById('table');
                viewSelect.innerHTML = '<option value="">Выберите представление</option>';
                // Заполняем выпадающий список представлениями
                views.forEach(view => {
                    const option = document.createElement('option');
                    option.value = view;
                    option.textContent = view;
                    viewSelect.appendChild(option);
                });

                // Запрашиваем список таблиц
                const responseTables = await fetch('/api/get_tables/', {
                    headers: { 'X-CSRFToken': getCookie('csrftoken') }
                });
                const tables = await responseTables.json();
                console.log('Loaded tables:', tables);
                const tableSelectRecords = document.getElementById('table_select');
                tableSelectRecords.innerHTML = '<option value="">Выберите таблицу</option>';
                // Заполняем выпадающий список таблицами
                tables.forEach(table => {
                    const option = document.createElement('option');
                    option.value = table;
                    option.textContent = table;
                    tableSelectRecords.appendChild(option);
                });
            } catch (error) {
                // Обрабатываем ошибку загрузки
                console.error('Error loading views/tables:', error);
                showMessage('Ошибка при загрузке списка представлений и таблиц.');
            }
        }

        // Обработчик отправки формы для создания или отображения сводки
        document.getElementById('summaryForm').addEventListener('submit', async (e) => {
            e.preventDefault(); // Предотвращаем стандартную отправку формы
            const form = e.target;
            const formData = new FormData(form);
            const view = formData.get('table'); // Получаем выбранное представление
            let action = formData.get('action'); // Получаем действие (create/display)

            // Определяем, какая кнопка была нажата
            const submitter = e.submitter;
            let submitButton = submitter && submitter.tagName === 'BUTTON' ? submitter : null;

            // Отладка данных формы
            console.log('Form elements:', Array.from(form.elements).map(el => ({ name: el.name, value: el.value })));

            // Если действие не определено, используем значение кнопки
            if (!action && submitButton) {
                action = submitButton.value;
                formData.append('action', action);
                console.log('Set action from submitter:', action);
            }
            // Если действие или кнопка не найдены, используем первую кнопку отправки
            if (!action || !submitButton) {
                console.warn('Action is null or button not found, using first submit button');
                submitButton = form.querySelector('button[type="submit"]');
                action = submitButton ? submitButton.value : null;
                if (action) {
                    formData.append('action', action);
                    console.log('Set action from fallback:', action);
                }
            }

            console.log('Submitting summary form:', { view, action, formData: Object.fromEntries(formData) });

            // Проверяем, выбрано ли представление
            if (!view) {
                console.error('View not selected');
                showMessage('Пожалуйста, выберите представление.');
                return;
            }

            // Проверяем, указано ли действие
            if (!action) {
                console.error('Action not specified');
                showMessage('Ошибка: действие не указано.');
                return;
            }

            // Блокируем кнопку во время запроса
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" aria-hidden="true"></span> Загрузка...';
            }

            try {
                // Отправляем запрос на генерацию сводки
                const response = await fetch('/api/generate_summary/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCookie('csrftoken') },
                    body: formData,
                });

                console.log('Response status:', response.status, 'Content-Type:', response.headers.get('Content-Type'));

                const contentType = response.headers.get('Content-Type') || '';

                // Обработка действия "display" (отобразить данные)
                if (action === 'display') {
                    if (contentType.includes('application/json')) {
                        const data = await response.json();
                        console.log('Received JSON data:', data);
                        if (data.success) {
                            displaySummaryData(data.data); // Отображаем данные в модальном окне
                        } else {
                            console.error('Server error:', data.error);
                            showMessage(`Ошибка: ${data.error}`);
                        }
                    } else {
                        console.error('Unexpected response type:', contentType);
                        showMessage('Ошибка: сервер вернул неверный формат данных.');
                    }
                // Обработка действия "create" (создать отчёт)
                } else if (action === 'create') {
                    if (contentType.includes('pdf') || contentType.includes('openxmlformats') || contentType.includes('msword')) {
                        const blob = await response.blob(); // Получаем файл как Blob
                        const contentDisposition = response.headers.get('Content-Disposition') || '';
                        let filename = `report.${formData.get('format')}`; // Устанавливаем имя файла по умолчанию
                        if (contentDisposition) {
                            const match = contentDisposition.match(/filename="(.+)"/);
                            if (match) filename = match[1]; // Извлекаем имя файла из заголовка
                        }
                        console.log('Downloading file:', filename);

                        // Создаём ссылку для скачивания файла
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = filename;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        window.URL.revokeObjectURL(url);

                        // Показываем сообщение об успешном создании отчёта
                        const modalBody = document.getElementById('summaryModalBody');
                        modalBody.innerHTML = `Отчет успешно сгенерирован и скачан!`;
                        new bootstrap.Modal(document.getElementById('summarySuccessModal')).show();
                    } else {
                        const errorData = await response.json();
                        console.error('Error response:', errorData);
                        showMessage(`Ошибка: ${errorData.error || 'Не удалось сформировать отчет.'}`);
                    }
                }
            } catch (error) {
                console.error('Fetch error:', error);
                showMessage(`Ошибка при отправке запроса: ${error.message}`);
            } finally {
                // Разблокируем кнопку после завершения запроса
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.textContent = action === 'create' ? 'Создать отчёт' : 'Вывести информацию';
                }
            }
        });

        // Асинхронная функция для загрузки данных таблицы
        async function loadTableData() {
            const tableName = document.getElementById('table_select').value;
            const tableContainer = document.getElementById('table_container');
            console.log('Loading table data for:', tableName);

            // Если таблица не выбрана, очищаем контейнер
            if (!tableName) {
                console.log('No table selected, clearing container');
                tableContainer.innerHTML = '';
                return;
            }

            try {
                // Запрашиваем данные таблицы
                const response = await fetch(`/api/get_table_data/?table=${tableName}`, {
                    headers: { 'X-CSRFToken': getCookie('csrftoken') },
                });
                console.log('Table data response:', response.status);

                const data = await response.json();
                console.log('Received table data:', data);

                // Проверяем успешность ответа
                if (!data.success) {
                    console.error('Server error:', data.error);
                    tableContainer.innerHTML = `<p>Ошибка: ${data.error}</p>`;
                    showMessage(`Ошибка загрузки данных: ${data.error}`);
                    return;
                }

                // Если данных нет, отображаем сообщение
                if (!data.data || data.data.length === 0) {
                    console.log('No data returned');
                    tableContainer.innerHTML = '<p>Нет данных для отображения.</p>';
                    return;
                }

                // Создаём HTML для таблицы
                let html = `
                    <table class="table table-striped table-editable">
                        <thead><tr>
                            ${Object.keys(data.data[0]).map(key => `<th>${key}</th>`).join('')}
                            <th>Действия</th>
                        </tr></thead>
                        <tbody>
                `;
                data.data.forEach(row => {
                    // Добавляем строки с полями ввода для редактирования
                    html += `<tr>${Object.keys(row).map(key => 
                        `<td><input type="text" value="${row[key] ?? ''}" data-field="${key}" data-id="${row.id}"></td>`
                    ).join('')}
                        <td><button type="button" class="btn btn-sm btn-primary save-btn" data-id="${row.id}">Сохранить</button></td></tr>`;
                });
                html += '</tbody></table>';
                tableContainer.innerHTML = html;

                // Добавляем обработчики для кнопок "Сохранить"
                document.querySelectorAll('.save-btn').forEach(button => {
                    button.addEventListener('click', () => {
                        const id = button.dataset.id;
                        const row = button.closest('tr');
                        const fields = {};
                        // Собираем данные из полей ввода
                        row.querySelectorAll('input').forEach(input => {
                            fields[input.dataset.field] = input.value;
                        });
                        console.log('Saving row:', { tableName, id, fields });
                        saveTableData(tableName, id, fields); // Сохраняем изменения
                    });
                });
            } catch (error) {
                console.error('Error loading table data:', error);
                tableContainer.innerHTML = '<p>Ошибка при загрузке данных.</p>';
                showMessage('Ошибка при получении данных таблицы.');
            }
        }

        // Асинхронная функция для сохранения изменений в таблице
        async function saveTableData(tableName, id, fields) {
            try {
                // Отправляем запрос на сохранение данных
                const response = await fetch('/api/save_table_data/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: JSON.stringify({ table: tableName, id, fields }),
                });
                console.log('Save response:', response.status);

                const data = await response.json();
                console.log('Received:', data);

                // Проверяем успешность сохранения
                if (data.success) {
                    console.log('Changes saved successfully.');
                    loadTableData(); // Обновляем таблицу
                    showMessage('Изменения сохранены!', 'success');
                } else {
                    console.error('Save error:', data.error);
                    showMessage(`Ошибка сохранения: ${data.error}`);
                }
            } catch (error) {
                console.error('Error saving data:', error);
                showMessage('Ошибка при сохранении данных.');
            }
        }

        // Асинхронная функция для загрузки динамических полей формы
        async function loadDynamicFields() {
            const tableName = document.getElementById('table_select').value;
            console.log('Loading dynamic fields for:', tableName);
            const tableNameInput = document.getElementById('table_name');
            const dynamicFields = document.getElementById('dynamic_fields');

            tableNameInput.value = tableName; // Устанавливаем имя таблицы

            // Если таблица не выбрана, очищаем поля
            if (!tableName) {
                dynamicFields.innerHTML = '';
                return;
            }

            try {
                // Запрашиваем поля таблицы
                const response = await fetch(`/api/get_table_fields/?table=${tableName}`, {
                    headers: { 'X-CSRFToken': getCookie('csrftoken') },
                });
                const fields = await response.json();
                console.log('Fields:', fields);

                // Если получен массив полей, создаём поля ввода
                if (Array.isArray(fields)) {
                    dynamicFields.innerHTML = fields.map(field => `
                        <div class="mb-3">
                            <label for="field_${field}_events" class="form-label">${field}</label>
                            <input type="text" class="form-control" id="field_${field}_events" name="${field}">
                        </div>
                    `).join('');
                } else {
                    console.error('Invalid fields response:', fields);
                    dynamicFields.innerHTML = '<p>Ошибка при загрузке полей.</p>';
                    showMessage('Ошибка при загрузке полей формы.');
                }
            } catch (error) {
                console.error('Error loading fields:', error);
                dynamicFields.innerHTML = '<p>Ошибка при загрузке полей.</p>';
                showMessage('Ошибка при загрузке полей формы.');
            }
        }

        // Обработчик отправки формы для добавления записи
        document.getElementById('recordForm').addEventListener('submit', async (e) => {
            e.preventDefault(); // Предотвращаем стандартную отправку формы
            const formData = new FormData(e.target);
            const tableName = formData.get('table_name');
            console.log('Submitting record form:', Object.fromEntries(formData));

            try {
                // Отправляем запрос на добавление записи
                const response = await fetch('/api/add_record/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCookie('csrftoken') },
                    body: formData,
                });
                console.log('Add record response:', response.status);

                const data = await response.json();
                console.log('Add record result:', data);

                // Проверяем успешность добавления
                if (data.success) {
                    console.log('Record added successfully');
                    loadTableData(); // Обновляем таблицу
                    bootstrap.Modal.getInstance(document.getElementById('addEditModal')).hide(); // Закрываем модальное окно
                    showMessage('Запись добавлена!', 'success');
                } else {
                    console.error('Error adding record:', data.error);
                    showMessage(`Ошибка: ${data.error}`);
                }
            } catch (error) {
                console.error('Error adding record:', error);
                showMessage('Ошибка при добавлении записи.');
            }
        });

        // Функция для очистки формы добавления записи
        function clearForm() {
            console.log('Clearing form');
            const recordId = document.getElementById('record_id');
            const tableNameInput = document.getElementById('table_name');
            const dynamicFields = document.getElementById('dynamic_fields');
            const tableSelect = document.getElementById('table_select');

            // Сбрасываем значения полей
            recordId.value = '';
            tableNameInput.value = '';
            dynamicFields.innerHTML = '';
            // Если таблица выбрана, загружаем поля
            if (tableSelect.value) {
                loadDynamicFields();
            }
        }

        // Привязываем очистку формы к кнопке добавления записи
        document.getElementById('addRecordButton').addEventListener('click', clearForm);

        // Функция для получения CSRF-токена из cookie
        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            console.log('Fetching CSRF token');
            return parts.length === 2 ? parts.pop().split(';').shift() : null;
        }

        // Инициализация панели управления
        console.log('Initializing control panel');
        loadViews(); // Загружаем представления и таблицы
        // Обработчик изменения выбора таблицы
        document.getElementById('table_select').addEventListener('change', () => {
            console.log('Table select changed');
            loadDynamicFields(); // Загружаем динамические поля
            loadTableData(); // Загружаем данные таблицы
        });

        // Проверяем, нужно ли показать модальное окно с сообщениями
        const hasMessages = document.body.dataset.hasMessages === 'true';
        if (hasMessages) {
            console.log('Showing messages modal');
            new bootstrap.Modal(document.getElementById('summarySuccessModal')).show();
        }
    });