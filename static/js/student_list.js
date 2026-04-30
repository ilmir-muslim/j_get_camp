// Функция для обновления нумерации строк
function updateRowNumbers() {
    const rows = document.querySelectorAll('#students-table tbody tr');
    rows.forEach((row, index) => {
        row.cells[0].textContent = index + 1;
    });
}

// Инициализация тултипов для ячеек special_notes
function initSpecialNotesTooltips() {
    document.querySelectorAll('.special-notes-cell').forEach(el => {
        if (!bootstrap.Tooltip.getInstance(el)) {
            const titleText = el.getAttribute('data-bs-title') || '';
            new bootstrap.Tooltip(el, { placement: 'top', trigger: 'hover', title: titleText });
        }
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
                                const row = document.getElementById(`student-${data.student.id}`);
                                if (row) {
                                    row.cells[2].textContent = data.student.full_name;
                                    row.cells[4].textContent = data.student.phone;
                                    row.cells[5].textContent = data.student.parent_name;
                                    row.cells[8].textContent = data.student.branch_name || '—';
                                    row.cells[9].textContent = data.student.attendance_type_display;
                                    row.cells[10].textContent = data.student.individual_price || data.student.default_price;
                                    row.cells[11].textContent = data.student.price_comment || '';
                                    const specialNotesCell = row.cells[12];
                                    const specialNotes = data.student.special_notes || '';
                                    specialNotesCell.textContent = specialNotes.length > 30 ? specialNotes.substring(0, 30) + '…' : specialNotes;
                                    specialNotesCell.setAttribute('data-bs-title', specialNotes);
                                    const oldTooltip = bootstrap.Tooltip.getInstance(specialNotesCell);
                                    if (oldTooltip) oldTooltip.dispose();
                                    new bootstrap.Tooltip(specialNotesCell, {
                                        placement: 'top',
                                        trigger: 'hover',
                                        title: specialNotes
                                    });
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
                    const row = document.getElementById(`student-${studentId}`);
                    if (row) {
                        row.remove();
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

// ===== ФУНКЦИЯ ПРЕДУПРЕЖДЕНИЯ О ДУБЛИКАТАХ =====
function showDuplicateWarning(duplicates, message, onConfirm) {
    const oldModal = document.getElementById('duplicateWarningModal');
    if (oldModal) oldModal.remove();

    const modalHtml = `
    <div class="modal fade" id="duplicateWarningModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header bg-warning text-dark">
            <h5 class="modal-title">⚠️ Возможные дубликаты</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <p>${message}</p>
            <ul class="list-group">
              ${duplicates.map(d =>
        `<li class="list-group-item"><strong>${d.full_name}</strong> (тел: ${d.phone || '—'}, родитель: ${d.parent_name || '—'})</li>`
    ).join('')}
            </ul>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Отмена</button>
            <button type="button" class="btn btn-warning" id="ignore-duplicates-btn">Игнорировать и создать</button>
          </div>
        </div>
      </div>
    </div>`;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modalEl = document.getElementById('duplicateWarningModal');
    const modal = new bootstrap.Modal(modalEl);
    modal.show();

    document.getElementById('ignore-duplicates-btn').addEventListener('click', () => {
        modal.hide();
        onConfirm();
    });
    modalEl.addEventListener('hidden.bs.modal', () => modalEl.remove());
}

// Обработчики событий
document.addEventListener('DOMContentLoaded', function () {
    initSpecialNotesTooltips();

    document.getElementById('add-student-btn').addEventListener('click', function () {
        const modal = new bootstrap.Modal(document.getElementById('createStudentModal'));
        modal.show();
    });

    // ===== ОБРАБОТЧИК СОХРАНЕНИЯ НОВОГО УЧЕНИКА =====
    document.getElementById('save-student-btn').addEventListener('click', function () {
        const form = document.getElementById('create-student-form');
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());

        const requestData = {
            full_name: data.full_name,
            phone: data.phone,
            parent_name: data.parent_name,
            attendance_type: data.attendance_type,
            default_price: data.default_price,
        };

        function sendCreateRequest(payload) {
            return fetch('/students/create/ajax/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: JSON.stringify(payload),
            }).then(res => res.json());
        }

        function handleStudentCreated(data) {
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
                <td>—</td>
                <td>${data.student.squad_name || '—'}</td>
                <td>—</td>
            `;
            tableBody.appendChild(newRow);
            updateRowNumbers();

            const specialNotesCell = newRow.querySelector('.special-notes-cell');
            if (specialNotesCell) {
                new bootstrap.Tooltip(specialNotesCell, { placement: 'top', trigger: 'hover', title: '' });
            }
            newRow.querySelector('.edit-student-btn').addEventListener('click', () => loadStudentEditForm(data.student.id));
            newRow.querySelector('.delete-student-btn').addEventListener('click', () => deleteStudent(data.student.id));

            form.reset();
            bootstrap.Modal.getInstance(document.getElementById('createStudentModal')).hide();
            showToast('Ученик успешно создан');
        }

        // Отправка запроса
        sendCreateRequest(requestData)
            .then(data => {
                console.log('Ответ сервера:', data);  // <-- для диагностики

                if (data.success) {
                    handleStudentCreated(data);
                } else if (data.duplicates) {
                    // ЗАКРЫВАЕМ модальное окно создания перед показом предупреждения
                    const createModal = bootstrap.Modal.getInstance(document.getElementById('createStudentModal'));
                    if (createModal) createModal.hide();

                    showDuplicateWarning(data.duplicates, data.message, () => {
                        const forceData = { ...requestData, force_create: true };
                        sendCreateRequest(forceData)
                            .then(data2 => {
                                console.log('Ответ сервера (force):', data2);
                                if (data2.success) {
                                    handleStudentCreated(data2);
                                } else {
                                    showToast(data2.error || 'Ошибка при создании ученика', 'error');
                                }
                            });
                    });
                } else {
                    // Настоящая ошибка
                    let errorMsg = 'Ошибка при создании ученика';
                    if (data.errors) {
                        try {
                            const errors = typeof data.errors === 'string' ? JSON.parse(data.errors) : data.errors;
                            errorMsg += ': ' + Object.values(errors).join(', ');
                        } catch {
                            errorMsg += ': ' + data.errors;
                        }
                    } else if (data.error) {
                        errorMsg += ': ' + data.error;
                    }
                    showToast(errorMsg, 'error');
                }
            })
            .catch(error => {
                console.error('Ошибка сети:', error);
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
            const nameCell = row.querySelector('td:nth-child(3)');
            const studentName = nameCell.textContent.toLowerCase();
            row.style.display = studentName.includes(searchText) ? '' : 'none';
        });
    });
});