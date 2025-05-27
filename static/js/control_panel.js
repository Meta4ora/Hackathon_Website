document.addEventListener('DOMContentLoaded', function () {
    // Динамическое отображение фильтров для сводок
    function toggleFilters() {
        const tableSelect = document.getElementById('summary_table');
        const filterFields = document.getElementById('filter_fields');
        if (tableSelect.value) {
            filterFields.style.display = 'block';
        } else {
            filterFields.style.display = 'none';
        }
    }

    // Загрузка данных таблицы
    function loadTableData() {
        const tableSelect = document.getElementById('table_select');
        const tableContainer = document.getElementById('table_container');
        const tableName = tableSelect.value;

        if (!tableName) {
            tableContainer.innerHTML = '';
            return;
        }

        fetch(`/api/get_table_data/?table=${tableName}`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
        })
            .then(response => response.json())
            .then(data => {
                let html = `
                    <table class="table table-striped table-editable">
                        <thead>
                            <tr>
                                ${Object.keys(data[0]).map(key => `<th>${key}</th>`).join('')}
                                <th>Действия</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                data.forEach(row => {
                    html += '<tr>';
                    Object.values(row).forEach((value, index) => {
                        html += `<td><input type="text" value="${value}" data-field="${Object.keys(row)[index]}" data-id="${row.id}"></td>`;
                    });
                    html += `
                        <td>
                            <button class="btn btn-sm btn-primary save-edit" data-id="${row.id}">Сохранить</button>
                        </td>
                    </tr>`;
                });
                html += '</tbody></table>';
                tableContainer.innerHTML = html;

                // Обработчик сохранения изменений
                document.querySelectorAll('.save-edit').forEach(button => {
                    button.addEventListener('click', function () {
                        const id = this.dataset.id;
                        const row = this.closest('tr');
                        const fields = {};
                        row.querySelectorAll('input').forEach(input => {
                            fields[input.dataset.field] = input.value;
                        });
                        saveEdit(tableName, id, fields);
                    });
                });
            })
            .catch(error => console.error('Ошибка загрузки данных:', error));
    }

    // Сохранение изменений
    function saveEdit(tableName, id, fields) {
        fetch(`/api/save_table_data/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ table: tableName, id: id, fields: fields }),
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    loadTableData();
                    alert('Изменения сохранены!');
                } else {
                    alert('Ошибка сохранения: ' + data.error);
                }
            })
            .catch(error => console.error('Ошибка сохранения:', error));
    }

    // Очистка формы для добавления
    function clearForm() {
        document.getElementById('record_id').value = '';
        document.getElementById('table_name').value = '';
        document.getElementById('dynamic_fields').innerHTML = '';
        const tableSelect = document.getElementById('table_select');
        if (tableSelect.value) {
            loadDynamicFields(tableSelect.value);
        }
    }

    // Загрузка динамических полей для формы
    function loadDynamicFields(tableName) {
        document.getElementById('table_name').value = tableName;
        fetch(`/api/get_table_fields/?table=${tableName}`, {
            method: 'GET',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
            },
        })
            .then(response => response.json())
            .then(fields => {
                let html = '';
                fields.forEach(field => {
                    html += `
                        <div class="mb-3">
                            <label for="${field}_input" class="form-label">${field}</label>
                            <input type="text" class="form-control" id="${field}_input" name="${field}">
                        </div>
                    `;
                });
                document.getElementById('dynamic_fields').innerHTML = html;
            })
            .catch(error => console.error('Ошибка загрузки полей:', error));
    }

    // Получение CSRF-токена
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Инициализация
    toggleFilters();
    loadTableData();
    document.getElementById('table_select').addEventListener('change', loadDynamicFields);
});