// JavaScript для страницы лидов
document.addEventListener('DOMContentLoaded', function () {
  // Функция для обновления нумерации строк
  function updateRowNumbers() {
    // Учитываем только видимые строки (не скрытые фильтрами)
    const rows = document.querySelectorAll('#leads-table tbody tr:not([style*="display: none"])');
    rows.forEach((row, index) => {
      row.cells[0].textContent = index + 1;
    });
  }


  // Функция для загрузки формы редактирования в модальное окно
  function loadLeadEditForm(leadId) {
    fetch(`/leads/edit/${leadId}/`, {
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
      .then(response => response.text())
      .then(html => {
        document.getElementById('lead-modal-content').innerHTML = html;
        const modal = new bootstrap.Modal(document.getElementById('leadModal'));
        modal.show();

        // Привязываем обработчик отправки формы после загрузки содержимого
        const form = document.getElementById('lead-edit-form');
        if (form) {
          form.addEventListener('submit', handleEditFormSubmit);
        }
      })
      .catch(error => {
        console.error('Error:', error);
        showToast('Произошла ошибка при загрузке формы', 'error');
      });
  }

  // Отдельная функция для обработки отправки формы редактирования
  function handleEditFormSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const formData = new FormData(form);
    const leadId = form.dataset.leadId;

    fetch(form.action, {
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
          updateLeadRow(data.lead);

          // Закрываем модальное окно
          const modal = bootstrap.Modal.getInstance(document.getElementById('leadModal'));
          modal.hide();

          showToast('Лид успешно обновлен');
        } else {
          showToast('Ошибка при обновлении лида', 'error');
        }
      })
      .catch(error => {
        console.error('Error:', error);
        showToast('Произошла ошибка при обновлении лида', 'error');
      });
  }

  // Функция для обновления строки лида в таблице
  function updateLeadRow(leadData) {
    const row = document.getElementById(`lead-${leadData.id}`);
    if (row) {
      // Обновляем статус
      const statusCell = row.cells[2];
      statusCell.innerHTML = `<span class="lead-status-${leadData.status}">${leadData.status_display}</span>`;

      // Обновляем остальные данные
      row.cells[3].textContent = leadData.source_display;
      row.cells[5].textContent = leadData.phone;
      row.cells[6].textContent = leadData.parent_name;
      row.cells[7].textContent = leadData.interest;
      row.cells[8].textContent = leadData.comment;

      // Обновляем дату перезвона и классы строки
      let callbackContent = '—';
      row.classList.remove('callback-danger', 'callback-warning');

      if (leadData.callback_date) {
        callbackContent = leadData.callback_date_formatted;

        if (leadData.is_callback_overdue) {
          row.classList.add('callback-danger');
          callbackContent += ' <i class="bi bi-exclamation-triangle-fill text-danger"></i>';
        } else if (leadData.is_callback_today) {
          row.classList.add('callback-warning');
          callbackContent += ' <i class="bi bi-bell-fill text-warning"></i>';
        }
      }

      row.cells[9].innerHTML = callbackContent;

      // Обновляем атрибуты данных
      row.dataset.status = leadData.status;
      row.dataset.source = leadData.source;
      row.dataset.name = leadData.parent_name;
    }
  }

  // Функция удаления лида
  function deleteLead(leadId) {
    if (confirm('Вы уверены, что хотите удалить этот лид?')) {
      fetch(`/leads/delete/${leadId}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': CSRF_TOKEN,
          'X-Requested-With': 'XMLHttpRequest',
        },
      })
        .then(response => {
          if (response.status === 200) {
            // Успешное удаление - сервер возвращает пустой ответ
            return { success: true };
          } else if (response.status === 204) {
            // Или если сервер возвращает статус 204 (No Content)
            return { success: true };
          } else {
            // Обработка ошибок
            return response.json().then(data => {
              return { success: false, message: data.message || 'Ошибка при удалении лида' };
            });
          }
        })
        .then(data => {
          if (data.success) {
            // Удаляем строку из таблицы
            const row = document.getElementById(`lead-${leadId}`);
            if (row) {
              row.remove();
              // Обновляем нумерацию после удаления
              updateRowNumbers();
              showToast('Лид успешно удален');
            }
          } else {
            showToast(data.message || 'Ошибка при удалении лида', 'error');
          }
        })
        .catch(error => {
          console.error('Error:', error);
          showToast('Произошла ошибка при удалении лида', 'error');
        });
    }
  }



  // Функция фильтрации таблицы
  function filterLeadsTable() {
    const statusFilter = document.getElementById('status-filter').value;
    const sourceFilter = document.getElementById('source-filter').value;

    document.querySelectorAll('#leads-table tbody tr').forEach(row => {
      const status = row.dataset.status;
      const source = row.dataset.source;

      // Проверяем соответствие фильтрам
      const statusMatch = !statusFilter || status === statusFilter;
      const sourceMatch = !sourceFilter || source === sourceFilter;

      // Показываем или скрываем строку в зависимости от соответствия фильтрам
      row.style.display = (statusMatch && sourceMatch) ? '' : 'none';
    });

    // Обновляем нумерацию после фильтрации
    updateRowNumbers();
  }

  // Функция сортировки таблицы
  function sortLeadsTable() {
    const sortValue = document.getElementById('sort-filter').value;
    if (!sortValue) return;

    const tableBody = document.querySelector('#leads-table tbody');
    const rows = Array.from(tableBody.querySelectorAll('tr:not([style*="display: none"])'));

    rows.sort((a, b) => {
      let valueA, valueB;

      switch (sortValue) {
        case 'date-desc':
          valueA = new Date(a.dataset.date);
          valueB = new Date(b.dataset.date);
          return valueB - valueA;

        case 'date-asc':
          valueA = new Date(a.dataset.date);
          valueB = new Date(b.dataset.date);
          return valueA - valueB;

        case 'name-asc':
          valueA = a.dataset.name.toLowerCase();
          valueB = b.dataset.name.toLowerCase();
          return valueA.localeCompare(valueB);

        case 'name-desc':
          valueA = a.dataset.name.toLowerCase();
          valueB = b.dataset.name.toLowerCase();
          return valueB.localeCompare(valueA);

        default:
          return 0;
      }
    });

    // Удаляем текущие строки
    while (tableBody.firstChild) {
      tableBody.removeChild(tableBody.firstChild);
    }

    // Добавляем отсортированные строки
    rows.forEach(row => {
      tableBody.appendChild(row);
    });

    // Обновляем нумерацию
    updateRowNumbers();
  }

  // Делегирование событий для кнопок редактирования и удаления
  document.getElementById('leads-table').addEventListener('click', function (e) {
    // Обработка кнопки редактирования
    if (e.target.closest('.edit-lead-btn')) {
      const button = e.target.closest('.edit-lead-btn');
      const leadId = button.dataset.leadId;
      loadLeadEditForm(leadId);
    }

    // Обработка кнопки удаления
    if (e.target.closest('.delete-lead-btn')) {
      const button = e.target.closest('.delete-lead-btn');
      const leadId = button.dataset.leadId;
      deleteLead(leadId);
    }
  });

  // Обработчик кнопки добавления лида
  document.getElementById('add-lead-btn').addEventListener('click', function () {
    const modal = new bootstrap.Modal(document.getElementById('createLeadModal'));
    modal.show();
  });

  // Обработчик кнопки сохранения нового лида
  document.getElementById('save-lead-btn').addEventListener('click', function () {
    const formData = new FormData(document.getElementById('create-lead-form'));

    fetch('/leads/create/ajax/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': CSRF_TOKEN,
      },
      body: formData
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Закрыть модальное окно и обновить таблицу
          $('#createLeadModal').modal('hide');
          location.reload(); // или динамически добавить строку в таблицу
        } else {
          // Показать ошибки
          console.error('Ошибки:', data.errors);
        }
      });
  });


  // Обработчики фильтров
  document.getElementById('status-filter').addEventListener('change', function () {
    filterLeadsTable();
    sortLeadsTable();
  });

  document.getElementById('source-filter').addEventListener('change', function () {
    filterLeadsTable();
    sortLeadsTable();
  });

  // Обработчик сортировки
  document.getElementById('sort-filter').addEventListener('change', sortLeadsTable);

  // Обработчик кнопки сброса фильтров
  document.getElementById('reset-filters').addEventListener('click', function () {
    document.getElementById('status-filter').value = '';
    document.getElementById('source-filter').value = '';
    document.getElementById('sort-filter').value = '';
    filterLeadsTable();
  });
});