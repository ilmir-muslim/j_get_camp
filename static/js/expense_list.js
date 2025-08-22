document.addEventListener('DOMContentLoaded', function () {
    // Функция для обновления порядковых номеров строк
    function updateRowNumbers() {
        const rows = document.querySelectorAll('#expenses-table-body tr');
        rows.forEach((row, index) => {
            row.cells[0].textContent = index + 1;
        });
    }

    // Функция для загрузки формы расхода
    function loadExpenseForm(url) {
        fetch(url)
            .then(response => response.text())
            .then(html => {
                document.getElementById('expense-modal-content').innerHTML = html;
                const modal = new bootstrap.Modal(document.getElementById('expenseModal'));
                modal.show();
            });
    }

    // Функция для обновления итоговой суммы расходов
    function updateExpensesTotal() {
        let total = 0;
        document.querySelectorAll('#expenses-table-body tr').forEach(row => {
            const amountCell = row.cells[4];
            const amount = parseFloat(amountCell.textContent);
            total += amount;
        });

        document.querySelector('.total-summary-row td:nth-child(2)').textContent = total.toFixed(2);
    }

    // Обновляем номера строк при загрузке страницы
    updateRowNumbers();

    // Обработчик для кнопки добавления расхода
    document.getElementById('add-expense-btn').addEventListener('click', function () {
        loadExpenseForm('/payroll/expenses/create/');
    });

    // Обработчик кликов по строкам расходов (для редактирования)
    document.querySelectorAll('.clickable-expense-row').forEach(row => {
        row.addEventListener('click', function (e) {
            // Игнорируем клики на кнопке удаления
            if (!e.target.closest('.delete-expense-btn')) {
                const expenseId = this.dataset.expenseId;
                loadExpenseForm(`/payroll/expenses/edit/${expenseId}/`);
            }
        });
    });

    // Обработчик кликов по кнопкам удаления
    document.addEventListener('click', function (e) {
        const deleteBtn = e.target.closest('.delete-expense-btn');
        if (deleteBtn) {
            const expenseId = deleteBtn.dataset.expenseId;

            if (confirm('Вы уверены, что хотите удалить этот расход?')) {
                fetch(`/payroll/expenses/delete/${expenseId}/`, {
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
                            const row = document.querySelector(`tr[data-expense-id="${expenseId}"]`);
                            if (row) row.remove();

                            // Обновляем порядковые номера
                            updateRowNumbers();

                            // Обновляем итоговую сумму
                            updateExpensesTotal();

                            // Показываем уведомление
                            showToast('Расход успешно удален', 'success');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showToast('Произошла ошибка при удалении расхода', 'error');
                    });
            }
        }
    });

    // Обработчик отправки формы расхода
    document.addEventListener('submit', function (e) {
        if (e.target.id === 'expense-form') {
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
                        // Закрываем модальное окно
                        const modal = bootstrap.Modal.getInstance(document.getElementById('expenseModal'));
                        if (modal) modal.hide();

                        // Обновляем таблицу расходов
                        const tableBody = document.getElementById('expenses-table-body');
                        const expenseRow = document.querySelector(`tr[data-expense-id="${data.expense.id}"]`);

                        if (expenseRow) {
                            // Обновляем существующую строку
                            expenseRow.innerHTML = `
              <td>${expenseRow.cells[0].textContent}</td>
              <td>${data.expense.schedule_name}</td>
              <td>${data.expense.category_display}</td>
              <td>${data.expense.comment || ''}</td>
              <td>${data.expense.amount}</td>
              <td>
                <button class="btn p-0 border-0 bg-transparent icon-btn delete-expense-btn"
                        data-expense-id="${data.expense.id}">
                  <i class="bi bi-trash text-danger fs-5"></i>
                </button>
              </td>
            `;
                        } else {
                            // Добавляем новую строку
                            const newRow = document.createElement('tr');
                            newRow.dataset.expenseId = data.expense.id;
                            newRow.className = 'clickable-expense-row';
                            newRow.innerHTML = `
              <td>0</td>
              <td>${data.expense.schedule_name}</td>
              <td>${data.expense.category_display}</td>
              <td>${data.expense.comment || ''}</td>
              <td>${data.expense.amount}</td>
              <td>
                <button class="btn p-0 border-0 bg-transparent icon-btn delete-expense-btn"
                        data-expense-id="${data.expense.id}">
                  <i class="bi bi-trash text-danger fs-5"></i>
                </button>
              </td>
            `;
                            tableBody.appendChild(newRow);

                            // Обновляем порядковые номера
                            updateRowNumbers();

                            // Добавляем обработчики для новой строки
                            newRow.addEventListener('click', function (e) {
                                if (!e.target.closest('.delete-expense-btn')) {
                                    const expenseId = this.dataset.expenseId;
                                    loadExpenseForm(`/payroll/expenses/edit/${expenseId}/`);
                                }
                            });
                        }

                        // Обновляем итоговую сумму
                        updateExpensesTotal();

                        // Показываем уведомление
                        showToast('Расход успешно сохранен', 'success');
                    } else {
                        // Обновляем содержимое модального окна с ошибками
                        document.getElementById('expense-modal-content').innerHTML = data.html;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast('Произошла ошибка при сохранении расхода', 'error');
                });
        }
    });
});