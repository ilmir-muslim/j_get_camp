// static/js/salary_list.js
document.addEventListener('DOMContentLoaded', function () {
    // Глобальные переменные
    let salariesData = [];
    const modal = new bootstrap.Modal(document.getElementById('salaryModal'));

    // Функция для показа уведомлений
    function showToast(message, type = 'info') {
        // Реализация из оригинального salary_list.html
        const toastContainer = document.getElementById('toast-container');
        const toastId = 'toast-' + Date.now();

        const toastEl = document.createElement('div');
        toastEl.className = `toast align-items-center text-white bg-${type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info'} border-0`;
        toastEl.setAttribute('role', 'alert');
        toastEl.setAttribute('aria-live', 'assertive');
        toastEl.setAttribute('aria-atomic', 'true');
        toastEl.id = toastId;

        toastEl.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;

        toastContainer.appendChild(toastEl);

        const toast = new bootstrap.Toast(toastEl, {
            autohide: true,
            delay: 3000
        });

        toast.show();

        // Удаляем toast из DOM после скрытия
        toastEl.addEventListener('hidden.bs.toast', function () {
            toastEl.remove();
        });
    }

    // Функция для обновления порядковых номеров строк
    function updateRowNumbers() {
        const rows = document.querySelectorAll('#salaries-table-body tr');
        rows.forEach((row, index) => {
            row.cells[0].textContent = index + 1;
        });
    }

    // Функция для загрузки данных о зарплатах
    async function loadSalariesData() {
        try {
            // В реальном приложении здесь будет fetch запрос к API
            // Для демонстрации используем данные из таблицы
            const tableBody = document.getElementById('salaries-table-body');
            salariesData = [];

            // Собираем данные из таблицы
            tableBody.querySelectorAll('tr').forEach(row => {
                const salary = {
                    id: row.dataset.salaryId,
                    employee: {
                        full_name: row.cells[2].textContent
                    },
                    schedule: {
                        name: row.cells[3].textContent.split(' (')[0],
                        start_date: row.cells[3].textContent.match(/\((.*?)\)/)[1].split(' - ')[0],
                        end_date: row.cells[3].textContent.match(/\((.*?)\)/)[1].split(' - ')[1]
                    },
                    payment_type: row.cells[4].textContent === 'Ежедневная' ? 'daily' : 'percent',
                    get_payment_type_display: row.cells[4].textContent,
                    days_worked: parseInt(row.cells[5].textContent),
                    days_worked_display: row.cells[5].textContent,
                    daily_rate: parseFloat(row.cells[6].textContent) || 0,
                    percent_rate: parseFloat(row.cells[7].textContent) || 0,
                    total_payment: parseFloat(row.cells[8].textContent),
                    is_paid: row.cells[9].querySelector('.status-paid') !== null
                };
                salariesData.push(salary);
            });

            updateSalaryTotal();

        } catch (error) {
            console.error('Ошибка при загрузке данных:', error);
            showToast('Произошла ошибка при загрузке данных', 'error');
        }
    }

    // Функция для обновления общей суммы
    function updateSalaryTotal() {
        const total = salariesData.reduce((sum, salary) => sum + salary.total_payment, 0);
        document.getElementById('total-salary-amount').textContent = total;
    }

    // Функция для загрузки формы зарплаты
    async function loadSalaryForm(salaryId = null) {
        try {
            // В реальном приложении здесь будет fetch запрос к серверу
            // Для демонстрации используем mock форму
            let url = '/payroll/salaries/create/';
            let method = 'GET';

            if (salaryId) {
                url = `/payroll/salaries/edit/${salaryId}/`;
            }

            const response = await fetch(url, {
                method: method,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });

            if (!response.ok) {
                throw new Error('Ошибка загрузки формы');
            }

            const html = await response.text();
            document.getElementById('salary-modal-content').innerHTML = html;

            // Если редактируем существующую запись, заполняем форму данными
            if (salaryId) {
                const salary = salariesData.find(s => s.id == salaryId);
                if (salary) {
                    // Заполняем форму данными
                    document.getElementById('id_employee').value = 1; // пример значения
                    document.getElementById('id_schedule').value = 1; // пример значения
                    document.getElementById('id_payment_type').value = salary.payment_type;
                    document.getElementById('id_days_worked').value = salary.days_worked;
                    document.getElementById('id_daily_rate').value = salary.daily_rate;
                    document.getElementById('id_percent_rate').value = salary.percent_rate;
                    document.getElementById('id_total_payment').value = salary.total_payment;
                    document.getElementById('id_is_paid').checked = salary.is_paid;
                }
            }

            // Добавляем обработчик события для формы
            const form = document.getElementById('salary-form');
            if (form) {
                form.addEventListener('submit', handleSalaryFormSubmit);
            }

            modal.show();

        } catch (error) {
            console.error('Ошибка при загрузке формы:', error);
            showToast('Произошла ошибка при загрузке формы', 'error');
        }
    }

    // Обработчик отправки формы зарплаты
    function handleSalaryFormSubmit(e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);
        const isEdit = form.action.includes('edit');

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': CSRF_TOKEN,
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    modal.hide();
                    showToast('Данные о зарплате успешно сохранены', 'success');

                    // Перезагружаем страницу для обновления данных
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                } else {
                    // Показываем ошибки валидации
                    if (data.errors) {
                        let errorMsg = '';
                        for (const field in data.errors) {
                            errorMsg += field + ': ' + data.errors[field].join(', ') + '\n';
                        }
                        alert('Ошибки:\n' + errorMsg);
                    } else {
                        alert('Неизвестная ошибка');
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('Произошла ошибка при сохранении данных', 'error');
            });
    }

    // Функция для удаления записи о зарплате
    function deleteSalary(salaryId) {
        if (confirm('Вы уверены, что хотите удалить эту запись о зарплате?')) {
            fetch(`/payroll/salaries/delete/${salaryId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': CSRF_TOKEN,
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Удаляем строку из таблицы
                        const row = document.querySelector(`tr[data-salary-id="${salaryId}"]`);
                        if (row) row.remove();

                        // Обновляем данные
                        loadSalariesData();

                        showToast('Запись о зарплате успешно удалена', 'success');
                    } else {
                        showToast('Ошибка при удалении записи', 'error');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('Произошла ошибка при удалении записи', 'error');
                });
        }
    }

    // Функция для добавления обработчиков событий к строкам таблицы
    function attachRowEventHandlers() {
        // Обработчик кликов по строкам зарплат (для редактирования)
        document.querySelectorAll('.clickable-salary-row').forEach(row => {
            row.addEventListener('click', function (e) {
                // Игнорируем клики на кнопке удаления
                if (!e.target.closest('.delete-salary-btn')) {
                    const salaryId = this.dataset.salaryId;
                    loadSalaryForm(salaryId);
                }
            });
        });

        // Обработчик кликов по кнопкам удаления
        document.querySelectorAll('.delete-salary-btn').forEach(btn => {
            btn.addEventListener('click', function (e) {
                e.stopPropagation(); // Предотвращаем срабатывание клика по строке
                const salaryId = this.dataset.salaryId;
                deleteSalary(salaryId);
            });
        });
    }

    // Инициализация при загрузке страницы
    function init() {
        // Загружаем данные о зарплатах
        loadSalariesData();

        // Добавляем обработчики событий
        attachRowEventHandlers();

        // Обработчик для кнопки добавления зарплаты
        document.getElementById('add-salary-btn').addEventListener('click', function () {
            loadSalaryForm();
        });

        // Обработчик для кнопки фильтрации невыплаченных
        document.getElementById('filter-unpaid-btn').addEventListener('click', function () {
            // Переключение состояния кнопки
            const isActive = this.classList.contains('btn-primary');

            if (isActive) {
                // Показываем все записи
                this.classList.remove('btn-primary');
                this.classList.add('btn-warning');
                document.querySelectorAll('.clickable-salary-row').forEach(row => {
                    row.style.display = '';
                });
                showToast('Показаны все записи о зарплатах', 'info');
            } else {
                // Фильтруем только невыплаченные
                this.classList.remove('btn-warning');
                this.classList.add('btn-primary');
                document.querySelectorAll('.clickable-salary-row').forEach(row => {
                    const isPaid = row.cells[9].querySelector('.status-paid') !== null;
                    row.style.display = isPaid ? 'none' : '';
                });
                showToast('Показаны только невыплаченные зарплаты', 'info');
            }

            // Обновляем нумерацию строк
            updateRowNumbers();
        });
    }

    // Запускаем инициализацию
    init();
});