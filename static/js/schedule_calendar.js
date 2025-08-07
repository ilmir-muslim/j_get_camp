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

// Основная функция инициализации
function initScheduleCalendar() {
    // Обработка кликов по ячейкам календаря
    document.querySelectorAll('.calendar-cell').forEach(cell => {
        cell.addEventListener('click', function(e) {
            if (e.target.classList.contains('calendar-cell')) {
                const branchId = this.dataset.branch;
                const weekStart = this.dataset.weekStart;
                const weekEnd = this.dataset.weekEnd;
                
                // Если в ячейке есть смены, переходим к деталям первой смены
                const scheduleCard = this.querySelector('.schedule-card');
                if (scheduleCard) {
                    const scheduleId = scheduleCard.dataset.id;
                    window.location.href = `/schedule/${scheduleId}/`;
                } 
                // Если ячейка пустая, открываем форму создания
                else {
                    createNewSchedule(branchId, weekStart, weekEnd);
                }
            }
        });
    });
    
    // Обработка кликов по пустым ячейкам
    document.querySelectorAll('.empty-cell').forEach(cell => {
        cell.addEventListener('click', function(e) {
            e.stopPropagation();
            const parentCell = this.closest('.calendar-cell');
            const branchId = parentCell.dataset.branch;
            const weekStart = parentCell.dataset.weekStart;
            const weekEnd = parentCell.dataset.weekEnd;
            createNewSchedule(branchId, weekStart, weekEnd);
        });
    });
    
    // Обработка кликов по карточкам смен
    document.querySelectorAll('.schedule-card').forEach(card => {
        card.addEventListener('click', function(e) {
            if (!e.target.classList.contains('edit-schedule-btn')) {
                const scheduleId = this.dataset.id;
                window.location.href = `/schedule/${scheduleId}/`;
            }
        });
    });
    
    // Обработка кликов по кнопкам редактирования
    document.querySelectorAll('.edit-schedule-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();
            const scheduleId = this.dataset.id;
            editSchedule(scheduleId);
        });
    });
    
    // Обработка кликов по названиям филиалов
    document.querySelectorAll('.branch-name, .branch-header').forEach(cell => {
        cell.addEventListener('click', function(e) {
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
    
    // Инициализация обработчиков формы
    initScheduleFormHandlers();
}

// Функция создания новой смены
function createNewSchedule(branchId, weekStart, weekEnd) {
    const url = `/schedule/quick_edit/?branch=${branchId}&week_start=${weekStart}&week_end=${weekEnd}`;
    
    fetch(url)
        .then(response => response.text())
        .then(html => {
            document.getElementById('modal-content').innerHTML = html;
            const modal = new bootstrap.Modal(document.getElementById('scheduleModal'));
            modal.show();
            
            // Переинициализация обработчиков для новой формы
            initScheduleFormHandlers();
        });
}

// Функция редактирования смены
function editSchedule(scheduleId) {
    const url = `/schedule/quick_edit/${scheduleId}/`;
    
    fetch(url)
        .then(response => response.text())
        .then(html => {
            document.getElementById('modal-content').innerHTML = html;
            const modal = new bootstrap.Modal(document.getElementById('scheduleModal'));
            modal.show();
            
            // Переинициализация обработчиков для новой формы
            initScheduleFormHandlers();
        });
}

// Инициализация обработчиков для формы
function initScheduleFormHandlers() {
    // Обработка отправки формы через AJAX
    const form = document.getElementById('schedule-quick-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const form = e.target;
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
            .then(response => {
                if (response.status === 200) {
                    return response.json();
                } else {
                    throw new Error('Server returned non-200 response');
                }
            })
            .then(data => {
                if (data.success) {
                    // Закрываем модальное окно
                    const modal = bootstrap.Modal.getInstance(document.getElementById('scheduleModal'));
                    if (modal) modal.hide();
                    
                    // Обновляем страницу
                    location.reload();
                } else {
                    // Обновляем содержимое модального окна с ошибками
                    document.getElementById('modal-content').innerHTML = data.html;
                    
                    // Повторно инициализируем обработчики для новой формы
                    initScheduleFormHandlers();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Произошла ошибка при сохранении. Пожалуйста, попробуйте снова.');
            });
        });
    }
    
    // Обработка удаления смены
    const deleteBtn = document.getElementById('delete-schedule');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            const scheduleId = this.dataset.id;
            if (confirm('Вы уверены, что хотите удалить эту смену?')) {
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

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', initScheduleCalendar);