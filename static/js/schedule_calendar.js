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

const CSRF_TOKEN = getCookie('csrftoken');

function showToast(message, type = 'info') {
    if (typeof window.showToast === 'function') {
        window.showToast(message, type);
        return;
    }
    const colors = { success: '#28a745', error: '#dc3545', info: '#17a2b8' };
    const toast = document.createElement('div');
    toast.textContent = message;
    toast.style.position = 'fixed';
    toast.style.bottom = '20px';
    toast.style.right = '20px';
    toast.style.backgroundColor = colors[type] || colors.info;
    toast.style.color = 'white';
    toast.style.padding = '10px 20px';
    toast.style.borderRadius = '5px';
    toast.style.zIndex = '9999';
    toast.style.boxShadow = '0 2px 10px rgba(0,0,0,0.2)';
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

function initScheduleCalendar() {
    document.querySelectorAll('.calendar-cell').forEach(cell => {
        cell.addEventListener('click', function (e) {
            if (e.target.classList.contains('calendar-cell')) {
                const branchId = this.dataset.branch;
                const weekStart = this.dataset.weekStart;
                const weekEnd = this.dataset.weekEnd;
                const scheduleCard = this.querySelector('.schedule-card');
                if (scheduleCard) {
                    const scheduleId = scheduleCard.dataset.id;
                    window.location.href = `/schedule/${scheduleId}/`;
                } else {
                    createNewSchedule(branchId, weekStart, weekEnd);
                }
            }
        });
    });

    document.querySelectorAll('.empty-cell').forEach(cell => {
        cell.addEventListener('click', function (e) {
            e.stopPropagation();
            const parentCell = this.closest('.calendar-cell');
            const branchId = parentCell.dataset.branch;
            const weekStart = parentCell.dataset.weekStart;
            const weekEnd = parentCell.dataset.weekEnd;
            createNewSchedule(branchId, weekStart, weekEnd);
        });
    });

    document.querySelectorAll('.schedule-card').forEach(card => {
        card.addEventListener('click', function (e) {
            if (!e.target.classList.contains('edit-schedule-btn')) {
                const scheduleId = this.dataset.id;
                window.location.href = `/schedule/${scheduleId}/`;
            }
        });
    });

    document.querySelectorAll('.edit-schedule-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            const scheduleId = this.dataset.id;
            editSchedule(scheduleId);
        });
    });

    document.querySelectorAll('.branch-name, .branch-header').forEach(cell => {
        cell.addEventListener('click', function (e) {
            e.stopPropagation();
            const branchId = this.dataset.branchId || this.dataset.branch;
            fetch(`/branches/${branchId}/details/`)
                .then(response => response.text())
                .then(html => {
                    document.getElementById('branch-modal-content').innerHTML = html;
                    const modal = new bootstrap.Modal(document.getElementById('branchModal'));
                    modal.show();
                });
        });
    });

    initScheduleFormHandlers();
    // initCreateStudentModal(); // УБРАЛИ ОТСЮДА
}

function createNewSchedule(branchId, weekStart, weekEnd) {
    const url = `/schedule/quick_edit/?branch=${branchId}&week_start=${weekStart}&week_end=${weekEnd}`;
    fetch(url)
        .then(response => response.text())
        .then(html => {
            document.getElementById('modal-content').innerHTML = html;
            const modal = new bootstrap.Modal(document.getElementById('scheduleModal'));
            modal.show();
            initScheduleFormHandlers();
        });
}

function editSchedule(scheduleId) {
    const url = `/schedule/quick_edit/${scheduleId}/`;
    fetch(url)
        .then(response => response.text())
        .then(html => {
            document.getElementById('modal-content').innerHTML = html;
            const modal = new bootstrap.Modal(document.getElementById('scheduleModal'));
            modal.show();
            initScheduleFormHandlers();
        });
}

function initScheduleFormHandlers() {
    const form = document.getElementById('schedule-quick-form');
    if (form) {
        form.addEventListener('submit', function (e) {
            e.preventDefault();
            const url = form.action;
            const formData = new FormData(form);
            fetch(url, {
                method: form.method,
                body: formData,
                headers: {
                    'X-CSRFToken': getCookie('csrftoken'),
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const modal = bootstrap.Modal.getInstance(document.getElementById('scheduleModal'));
                        if (modal) modal.hide();
                        location.reload();
                    } else {
                        document.getElementById('modal-content').innerHTML = data.html;
                        initScheduleFormHandlers();
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Ошибка при сохранении.');
                });
        });
    }
    const deleteBtn = document.getElementById('delete-schedule');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function () {
            const scheduleId = this.dataset.id;
            if (confirm('Удалить смену?')) {
                fetch(`/schedule/delete/${scheduleId}/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                    .then(response => {
                        if (response.ok) {
                            const modal = bootstrap.Modal.getInstance(document.getElementById('scheduleModal'));
                            if (modal) modal.hide();
                            location.reload();
                        }
                    });
            }
        });
    }
}

// ========== ПОИСК СТУДЕНТА ==========
function initStudentSearch() {
    const searchInput = document.getElementById('studentSearchInput');
    const suggestionsBox = document.getElementById('studentSuggestions');
    const searchResultsContainer = document.getElementById('searchResultsContainer');
    const searchResultsList = document.getElementById('searchResultsList');
    const calendarContainer = document.getElementById('calendarContainer');
    let debounceTimer;

    if (!searchInput) return;

    function toggleView(showResults) {
        if (showResults) {
            calendarContainer.style.display = 'none';
            searchResultsContainer.style.display = 'block';
        } else {
            calendarContainer.style.display = 'block';
            searchResultsContainer.style.display = 'none';
            searchResultsList.innerHTML = '';
        }
    }

    function hideSuggestions() {
        suggestionsBox.style.display = 'none';
        suggestionsBox.innerHTML = '';
    }

    function showSuggestions(students) {
        suggestionsBox.innerHTML = '';
        if (!students.length) {
            hideSuggestions();
            return;
        }
        students.forEach(student => {
            const item = document.createElement('button');
            item.className = 'dropdown-item';
            item.type = 'button';
            item.textContent = student.full_name;
            item.addEventListener('click', function () {
                searchInput.value = student.full_name;
                hideSuggestions();
                fetchStudentSchedules(student.id, student.full_name);
            });
            suggestionsBox.appendChild(item);
        });
        suggestionsBox.style.display = 'block';
    }

    function fetchStudentSuggestions(query) {
        if (query.length < 2) {
            hideSuggestions();
            return;
        }
        fetch(`${scheduleSearchStudentsUrl}?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                showSuggestions(data.students || []);
            })
            .catch(() => hideSuggestions());
    }

    function fetchStudentSchedules(studentId, studentName) {
        fetch(`${scheduleSearchByStudentUrl}?student_id=${encodeURIComponent(studentId)}`)
            .then(res => res.json())
            .then(data => {
                searchResultsList.innerHTML = '';
                const header = document.querySelector('#searchResultsContainer h4');
                if (header) {
                    header.textContent = `Смены с участием ученика: ${data.student_name || studentName}`;
                }
                if (!data.schedules.length) {
                    searchResultsList.innerHTML = '<p class="text-muted p-3">Смен не найдено</p>';
                } else {
                    data.schedules.forEach(schedule => {
                        const item = document.createElement('a');
                        item.href = `/schedule/${schedule.id}/`;
                        item.className = 'list-group-item list-group-item-action';
                        item.innerHTML = `
                            <div class="d-flex justify-content-between align-items-center">
                                <div>
                                    <strong>${schedule.name}</strong> 
                                    <span class="text-muted">(${schedule.theme})</span><br>
                                    <small>${schedule.start_date} – ${schedule.end_date}</small>
                                    <span class="badge bg-secondary ms-2">${schedule.branch}</span>
                                </div>
                                <i class="bi bi-chevron-right"></i>
                            </div>`;
                        searchResultsList.appendChild(item);
                    });
                }
                toggleView(true);
            });
    }

    searchInput.addEventListener('input', function () {
        clearTimeout(debounceTimer);
        const query = this.value.trim();
        if (query.length === 0) {
            toggleView(false);
            hideSuggestions();
            return;
        }
        debounceTimer = setTimeout(() => fetchStudentSuggestions(query), 300);
    });

    searchInput.addEventListener('focus', function () {
        const query = this.value.trim();
        if (query.length >= 2) {
            fetchStudentSuggestions(query);
        }
    });

    document.addEventListener('click', function (e) {
        if (!searchInput.contains(e.target) && !suggestionsBox.contains(e.target)) {
            hideSuggestions();
        }
    });

    toggleView(false);
}

// ========== МОДАЛЬНОЕ ОКНО СОЗДАНИЯ УЧЕНИКА (с защитой от двойной инициализации) ==========
let studentModalInitialized = false;

function initCreateStudentModal() {
    if (studentModalInitialized) return;
    studentModalInitialized = true;

    const createBtn = document.getElementById('create-student-btn');
    const modalElement = document.getElementById('createStudentModal');

    if (!createBtn || !modalElement) return;

    // Открытие модального окна
    createBtn.addEventListener('click', function () {
        const modal = new bootstrap.Modal(modalElement);
        modal.show();
    });

    const saveBtn = document.getElementById('save-student-btn');
    if (!saveBtn) return;

    saveBtn.addEventListener('click', function (e) {
        e.preventDefault();
        const btn = this;
        const originalText = btn.innerHTML;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Сохранение...';
        btn.disabled = true;

        const full_name = document.getElementById('full_name')?.value.trim();
        const phone = document.getElementById('phone')?.value || '';
        const parent_name = document.getElementById('parent_name')?.value || '';
        const attendance_type = document.getElementById('attendance_type')?.value || 'full_day';
        const default_price = document.getElementById('default_price')?.value || '11400';

        if (!full_name) {
            showToast('ФИО ученика обязательно', 'error');
            btn.innerHTML = originalText;
            btn.disabled = false;
            return;
        }

        const requestData = {
            full_name, phone, parent_name, attendance_type, default_price,
            schedule_id: null
        };

        function sendCreateRequest(data) {
            return fetch('/students/create/ajax/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
                body: JSON.stringify(data)
            }).then(res => res.json());
        }

        function handleStudentCreated() {
            const modal = bootstrap.Modal.getInstance(modalElement);
            if (modal) modal.hide();

            document.getElementById('full_name').value = '';
            document.getElementById('phone').value = '';
            document.getElementById('parent_name').value = '';
            document.getElementById('default_price').value = '11400';

            showToast('Ученик успешно создан', 'success');
            btn.innerHTML = originalText;
            btn.disabled = false;

            // Убираем возможный остаточный backdrop
            const backdrops = document.querySelectorAll('.modal-backdrop');
            backdrops.forEach(backdrop => backdrop.remove());
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
        }

        function showDuplicateWarning(duplicates, message, onConfirm) {
            let oldModal = document.getElementById('duplicateWarningModal');
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
                      ${duplicates.map(d => `<li class="list-group-item"><strong>${d.full_name}</strong> (тел: ${d.phone || '—'}, родитель: ${d.parent_name || '—'})</li>`).join('')}
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

        sendCreateRequest(requestData)
            .then(data => {
                if (data.success) {
                    handleStudentCreated();
                } else if (data.duplicates) {
                    const mainModal = bootstrap.Modal.getInstance(modalElement);
                    if (mainModal) mainModal.hide();

                    btn.innerHTML = originalText;
                    btn.disabled = false;
                    showDuplicateWarning(data.duplicates, data.message, () => {
                        btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Создание...';
                        btn.disabled = true;
                        sendCreateRequest({ ...requestData, force_create: true })
                            .then(data2 => {
                                if (data2.success) {
                                    handleStudentCreated();
                                } else {
                                    showToast(data2.error || 'Ошибка создания', 'error');
                                    btn.innerHTML = originalText;
                                    btn.disabled = false;
                                }
                            });
                    });
                } else {
                    let errorMsg = 'Ошибка: ' + (data.error || 'неизвестная ошибка');
                    showToast(errorMsg, 'error');
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                }
            })
            .catch(error => {
                console.error(error);
                showToast('Ошибка соединения', 'error');
                btn.innerHTML = originalText;
                btn.disabled = false;
            });
    });
}

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', function () {
    initScheduleCalendar();
    initStudentSearch();
    if (document.getElementById('createStudentModal')) {
        initCreateStudentModal();
    }
});