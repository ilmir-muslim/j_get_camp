// Функция для обновления нумерации строк
function updateRowNumbers() {
    const rows = document.querySelectorAll('#students-table tbody tr');
    rows.forEach((row, index) => {
        row.cells[0].textContent = index + 1;
    });
}

// Функция для загрузки формы редактирования в модальное окно
function loadStudentEditForm(studentId) {
    fetch(`/students/${studentId}/quick_edit/`)
        .then(response => response.text())
        .then(html => {
            document.getElementById('student-modal-content').innerHTML = html;
            const modal = new bootstrap.Modal(document.getElementById('studentModal'));
            modal.show();

            // Обработчик отправки формы редактирования
            const form = document.getElementById('student-quick-edit-form');
            if (form) {
                form.addEventListener('submit', function (e) {
                    e.preventDefault();
                    const formData = new FormData(this);

                    fetch(this.action, {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-CSRFToken': CSRF_TOKEN,
                            'X-Requested-With': 'XMLHttpRequest',
                        },
                    })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                // Обновляем данные в таблице
                                const row = document.getElementById(`student-${data.student.id}`);
                                if (row) {
                                    row.cells[2].textContent = data.student.full_name;
                                    row.cells[4].textContent = data.student.phone;
                                    row.cells[5].textContent = data.student.parent_name;
                                    row.cells[6].textContent = data.student.schedule_name || '—';
                                    // Обновляем филиал
                                    row.cells[7].textContent = data.student.branch_name || '—';
                                    row.cells[8].textContent = data.student.attendance_type_display;
                                    row.cells[9].textContent = data.student.individual_price || data.student.default_price;
                                    row.cells[10].textContent = data.student.price_comment || '';
                                }

                                modal.hide();
                                showToast('Ученик успешно обновлен');
                            } else {
                                showToast('Ошибка при обновлении ученика', 'error');
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            showToast('Произошла ошибка при обновлении ученика', 'error');
                        });
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showToast('Произошла ошибка при загрузке формы', 'error');
        });
}

// Функция удаления ученика
function deleteStudent(studentId) {
    if (confirm('Вы уверены, что хотите удалить этого ученика?')) {
        fetch(`/students/delete/${studentId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Удаляем строку из таблицы
                    const row = document.getElementById(`student-${studentId}`);
                    if (row) {
                        row.remove();
                        // Обновляем нумерацию после удаления
                        updateRowNumbers();
                        showToast('Ученик успешно удален');
                    }
                } else {
                    showToast('Ошибка при удалении ученика', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Произошла ошибка при удалении ученика', 'error');
            });
    }
}

// Обработчики событий
document.addEventListener('DOMContentLoaded', function () {
    // Обработчик кнопки добавления ученика
    document.getElementById('add-student-btn').addEventListener('click', function () {
        const modal = new bootstrap.Modal(document.getElementById('createStudentModal'));
        modal.show();
    });

    // Обработчик кнопки сохранения нового ученика
    document.getElementById('save-student-btn').addEventListener('click', function () {
        const formData = new FormData(document.getElementById('create-student-form'));
        const data = Object.fromEntries(formData.entries());

        fetch('/students/create/ajax/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify(data),
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Добавляем нового ученика в таблицу
                    const tableBody = document.querySelector('#students-table tbody');
                    const newRow = document.createElement('tr');
                    newRow.id = `student-${data.student.id}`;
                    newRow.innerHTML = `
                    <td>${tableBody.children.length + 1}</td>
                    <td>
                        <button class="btn p-0 border-0 bg-transparent icon-btn edit-student-btn"
                                data-student-id="${data.student.id}">
                            <i class="bi bi-pencil text-primary"></i>
                        </button>
                        <button class="btn p-0 border-0 bg-transparent icon-btn delete-student-btn"
                                data-student-id="${data.student.id}">
                            <i class="bi bi-trash text-danger"></i>
                        </button>
                    </td>
                    <td>${data.student.full_name}</td>
                    <td class="balance-cell" id="balance-${data.student.id}">0</td>
                    <td>${data.student.phone || ''}</td>
                    <td>${data.student.parent_name || ''}</td>
                    <td>${data.student.schedule_name || '—'}</td>
                    <td>${data.student.branch_name || '—'}</td>
                    <td>${data.student.attendance_type_display}</td>
                    <td>${data.student.individual_price || data.student.default_price}</td>
                    <td>${data.student.price_comment || ''}</td>
                `;

                    tableBody.appendChild(newRow);
                    updateRowNumbers();

                    // Добавляем обработчики для новых кнопок
                    newRow.querySelector('.edit-student-btn').addEventListener('click', function () {
                        loadStudentEditForm(data.student.id);
                    });

                    newRow.querySelector('.delete-student-btn').addEventListener('click', function () {
                        deleteStudent(data.student.id);
                    });

                    // Очищаем форму
                    document.getElementById('create-student-form').reset();
                    // Закрываем модальное окно и показываем уведомление
                    bootstrap.Modal.getInstance(document.getElementById('createStudentModal')).hide();
                    showToast('Ученик успешно создан');
                } else {
                    showToast('Ошибка при создании ученика', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Произошла ошибка при создании ученика', 'error');
            });
    });

    // Обработчики кнопок редактирования
    document.querySelectorAll('.edit-student-btn').forEach(button => {
        button.addEventListener('click', function () {
            const studentId = this.dataset.studentId;
            loadStudentEditForm(studentId);
        });
    });

    // Обработчики кнопок удаления
    document.querySelectorAll('.delete-student-btn').forEach(button => {
        button.addEventListener('click', function () {
            const studentId = this.dataset.studentId;
            deleteStudent(studentId);
        });
    });

    // Поиск учеников
    document.getElementById('student-search').addEventListener('input', function (e) {
        const searchText = e.target.value.toLowerCase();
        const rows = document.querySelectorAll('#students-table tbody tr');

        rows.forEach(row => {
            const nameCell = row.querySelector('td:nth-child(3)'); // Столбец с ФИО
            const studentName = nameCell.textContent.toLowerCase();

            if (studentName.includes(searchText)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
});