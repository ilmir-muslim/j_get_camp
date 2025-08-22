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
                                    row.cells[3].textContent = data.student.full_name;
                                    row.cells[4].textContent = data.student.phone;
                                    row.cells[5].textContent = data.student.parent_name;
                                    row.cells[6].textContent = data.student.schedule_name || '—';
                                    row.cells[7].textContent = data.student.attendance_type_display;
                                    row.cells[8].textContent = data.student.individual_price || data.student.default_price;
                                    row.cells[9].textContent = data.student.price_comment || '';
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

// Функция для загрузки истории баланса
function loadBalanceHistory(studentId) {
    fetch(`/students/${studentId}/balance_history/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const historyBody = document.getElementById('balance-history-body');
                const emptyMessage = document.getElementById('balance-history-empty');

                // Очищаем предыдущие данные
                historyBody.innerHTML = '';

                if (data.operations.length > 0) {
                    emptyMessage.classList.add('d-none');

                    // Заполняем таблицу данными
                    data.operations.forEach(operation => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${operation.date}</td>
                            <td>${operation.operation_type}</td>
                            <td class="${operation.operation_type === 'Пополнение' ? 'text-success' : 'text-danger'}">
                                ${operation.amount} руб.
                            </td>
                            <td>${operation.comment}</td>
                            <td>${operation.created_by}</td>
                        `;
                        historyBody.appendChild(row);
                    });
                } else {
                    emptyMessage.classList.remove('d-none');
                }
            } else {
                console.error('Ошибка при загрузке истории баланса');
            }
        })
        .catch(error => {
            console.error('Ошибка при загрузке истории баланса:', error);
        });
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
                <button class="btn p-0 border-0 bg-transparent icon-btn add-balance-btn"
                        data-student-id="${data.student.id}"
                        data-bs-toggle="tooltip" title="Пополнить баланс">
                  <i class="bi bi-wallet2 text-success"></i>
                </button>
              </td>
              <td>${data.student.full_name}</td>
              <td class="balance-cell" id="balance-${data.student.id}">0 руб.</td>
              <td>${data.student.phone || ''}</td>
              <td>${data.student.parent_name || ''}</td>
              <td>—</td>
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

                    newRow.querySelector('.add-balance-btn').addEventListener('click', function () {
                        const studentId = this.dataset.studentId;
                        document.getElementById('balance-student-id').value = studentId;
                        document.getElementById('balance-amount').value = '';
                        document.getElementById('balance-comment').value = '';

                        // Загружаем историю баланса при открытии модального окна
                        loadBalanceHistory(studentId);

                        const modal = new bootstrap.Modal(document.getElementById('balanceModal'));
                        modal.show();
                    });

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

    // Обработчик кнопки пополнения баланса
    document.querySelectorAll('.add-balance-btn').forEach(button => {
        button.addEventListener('click', function () {
            const studentId = this.dataset.studentId;
            document.getElementById('balance-student-id').value = studentId;
            document.getElementById('balance-amount').value = '';
            document.getElementById('balance-comment').value = '';

            // Загружаем историю баланса при открытии модального окна
            loadBalanceHistory(studentId);

            const modal = new bootstrap.Modal(document.getElementById('balanceModal'));
            modal.show();
        });
    });

    // Обработчик переключения вкладок
    document.getElementById('balanceTabs').addEventListener('shown.bs.tab', function (event) {
        const targetTab = event.target.getAttribute('data-bs-target');
        if (targetTab === '#history') {
            const studentId = document.getElementById('balance-student-id').value;
            loadBalanceHistory(studentId);
        }
    });

    // Обработчик сохранения баланса
    document.getElementById('save-balance-btn').addEventListener('click', function () {
        const formData = new FormData(document.getElementById('balance-form'));
        const studentId = formData.get('student_id');

        fetch(`/students/${studentId}/add_balance/`, {
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
                    // Обновляем отображение баланса в таблице
                    document.getElementById(`balance-${studentId}`).textContent =
                        `${data.new_balance} руб.`;

                    // Закрываем модальное окно
                    bootstrap.Modal.getInstance(document.getElementById('balanceModal')).hide();

                    showToast(data.message);
                } else {
                    if (data.errors) {
                        const errors = JSON.parse(data.errors);
                        let errorMessage = 'Ошибка при пополнении баланса: ';
                        for (const field in errors) {
                            errorMessage += errors[field].join(', ') + ' ';
                        }
                        showToast(errorMessage, 'error');
                    } else {
                        showToast(data.error || 'Ошибка при пополнении баланса', 'error');
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Произошла ошибка при пополнении баланса', 'error');
            });
    });

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
    
    // При закрытии модального окна активируем вкладку пополнения
    document.getElementById('balanceModal').addEventListener('hidden.bs.modal', function () {
        const addBalanceTab = new bootstrap.Tab(document.getElementById('add-balance-tab'));
        addBalanceTab.show();
    });
});