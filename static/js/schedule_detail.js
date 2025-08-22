document.addEventListener('DOMContentLoaded', function () {
  colorizePaymentCells();

  // Функция для загрузки формы в модальное окно
  function loadFormIntoModal(url) {
    fetch(url)
      .then(response => response.text())
      .then(html => {
        document.getElementById('universalFormModalContent').innerHTML = html;
        const modal = new bootstrap.Modal(document.getElementById('universalFormModal'));
        modal.show();
      });
  }

  // Вызываем при загрузке страницы
  document.addEventListener('DOMContentLoaded', function () {
    updatePaymentButtonsText();
  });

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

  // Функция для загрузки формы платежа
  function loadPaymentForm(url) {
    fetch(url, {
      credentials: 'include'
    })
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.text();
      })
      .then(html => {
        document.getElementById('payment-modal-content').innerHTML = html;
        const modal = new bootstrap.Modal(document.getElementById('paymentModal'));
        modal.show();

        // Инициализируем вкладки
        initPaymentTabs();
      })
      .catch(error => {
        console.error('Error loading payment form:', error);
        showToast('Ошибка при загрузке формы платежа', 'error');
      });
  }

  // Функция инициализации вкладок платежа
  function initPaymentTabs() {
    const triggerTabList = document.querySelectorAll('#paymentTabs button');
    triggerTabList.forEach(triggerEl => {
      triggerEl.addEventListener('click', function (event) {
        event.preventDefault();
        const tab = bootstrap.Tab.getInstance(this);
        if (!tab) {
          new bootstrap.Tab(this).show();
        } else {
          tab.show();
        }

        // При переключении на вкладку истории загружаем данные
        if (this.id === 'history-tab') {
          loadPaymentHistory();
        }
      });
    });

    // Загружаем баланс при открытии модального окна
    updatePaymentFormBalance();
  }

  // Функция обновления баланса в форме платежа
  function updatePaymentFormBalance() {
    const studentId = document.querySelector('#payment-form input[name="student"]').value;
    const amountInput = document.querySelector('#payment-form input[name="amount"]');

    fetch(`/students/${studentId}/check_balance/`)
      .then(response => response.json())
      .then(data => {
        if (data.balance !== undefined) {
          document.getElementById('current-balance').textContent =
            `${data.balance.toLocaleString('ru-RU')} руб.`;

          // Проверяем достаточно ли средств
          if (amountInput && amountInput.value) {
            const amount = parseFloat(amountInput.value);
            if (amount > data.balance) {
              document.getElementById('balance-warning').classList.remove('d-none');
            } else {
              document.getElementById('balance-warning').classList.add('d-none');
            }
          }
        }
      });
  }

  // Функция загрузки истории платежей
  function loadPaymentHistory() {
    const form = document.querySelector('#payment-form');
    if (!form) return;

    const studentId = form.querySelector('input[name="student"]').value;
    const scheduleId = form.querySelector('input[name="schedule"]').value;

    fetch(`/students/${studentId}/payments/history/?schedule_id=${scheduleId}`)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        if (data.success) {
          const historyContainer = document.getElementById('payment-history-content');
          historyContainer.innerHTML = data.html;
        } else {
          console.error('Error loading payment history:', data.error);
          const historyContainer = document.getElementById('payment-history-content');
          historyContainer.innerHTML = '<div class="text-center text-muted">Ошибка загрузки истории</div>';
        }
      })
      .catch(error => {
        console.error('Error loading payment history:', error);
        const historyContainer = document.getElementById('payment-history-content');
        historyContainer.innerHTML = '<div class="text-center text-muted">Ошибка загрузки истории</div>';
      });
  }


  // Функция для обновления нумерации строк в таблице сотрудников
  function updateEmployeeRowNumbers() {
    const tableBody = document.getElementById('employees-table');
    const rows = tableBody.querySelectorAll('tr:not([style*="display: none"])');
    rows.forEach((row, index) => {
      row.cells[0].textContent = index + 1;
    });
  }

  // Функция для обновления нумерации строк в таблице учеников
  function updateStudentRowNumbers() {
    const tableBody = document.getElementById('attendance-body');
    const rows = tableBody.querySelectorAll('tr:not([style*="display: none"])');
    rows.forEach((row, index) => {
      row.cells[0].textContent = index + 1;
    });
  }

  // Функция для обработки кликов по ячейкам посещаемости
  function handleAttendanceClick(event) {
    const cell = event.target.closest('.attendance-cell');
    if (!cell) return;

    // Проверяем, это сотрудник или ученик
    const employeeId = cell.dataset.employeeId;
    const studentId = cell.dataset.studentId;
    const date = cell.dataset.date;

    if (employeeId) {
      // Обработка посещаемости сотрудника
      fetch(`/schedule/${SCHEDULE_ID}/toggle_attendance/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRF_TOKEN
        },
        body: JSON.stringify({
          employee_id: employeeId,
          date: date
        })
      })
        .then(response => response.json())
        .then(data => {
          if (data.status === 'success') {
            updateAttendanceCell(cell, data);

            // Обновляем счетчик посещений сотрудника
            if (data.employee_id) {
              const row = document.getElementById(`employee-${data.employee_id}`);
              if (row) {
                const countCell = row.querySelector('td:nth-child(6)');
                if (countCell) {
                  countCell.textContent = data.total_attendance;
                }
              }
            }
            updateAttendanceTotals(); // Обновляем итоги
          }
        })
        .catch(error => console.error('Error:', error));
    }
    else if (studentId) {
      // Обработка посещаемости ученика
      fetch(`/schedule/${SCHEDULE_ID}/toggle_attendance/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRF_TOKEN
        },
        body: JSON.stringify({
          student_id: studentId,
          date: date
        })
      })
        .then(response => response.json())
        .then(data => {
          if (data.status === 'success') {
            updateAttendanceCell(cell, data);
            updateAttendanceCounter(studentId, data.total_attendance);
            updateAttendanceTotals(); // Обновляем итоги
          }
        })
        .catch(error => console.error('Error:', error));
    }
  }

  // Обновление внешнего вида ячейки
  function updateAttendanceCell(cell, data) {
    cell.classList.remove('bg-success', 'bg-warning', 'bg-danger');

    if (data.present) {
      cell.classList.add('bg-success');
      cell.innerHTML = '<i class="bi bi-check-lg text-white"></i>';
      cell.dataset.attendanceType = 'present';
    }
    else if (data.excused) {
      cell.classList.add('bg-warning');
      cell.innerHTML = '<i class="bi bi-exclamation-lg text-white"></i>';
      cell.dataset.attendanceType = 'excused';
    }
    else {
      cell.classList.add('bg-danger');
      cell.innerHTML = '<i class="bi bi-x-lg text-white"></i>';
      cell.dataset.attendanceType = 'absent';
    }
  }

  // Обновление счетчика посещений
  function updateAttendanceCounter(studentId, count) {
    const row = document.querySelector(`tr[data-student-id="${studentId}"]`);
    if (!row) return;

    const countCell = row.querySelector('td:nth-child(7)');
    if (countCell) {
      countCell.textContent = count;
      row.dataset.visits = count;
    }
  }

  // Функция для обновления итогов посещаемости
  function updateAttendanceTotals() {
    // Для сотрудников
    DATES_JSON.forEach(date => {
      const employeeCells = document.querySelectorAll(
        `#employees-table .attendance-cell[data-date="${date}"][data-attendance-type="present"]`
      );
      const count = employeeCells.length;
      const totalCell = document.querySelector(`#employee-total-row td[data-date="${date}"] .present-count`);
      if (totalCell) {
        totalCell.textContent = count;
      }
    });

    // Для учеников
    DATES_JSON.forEach(date => {
      const studentCells = document.querySelectorAll(
        `#attendance-body .attendance-cell[data-date="${date}"][data-attendance-type="present"]`
      );
      const count = studentCells.length;
      const totalCell = document.querySelector(`#student-total-row td[data-date="${date}"] .present-count`);
      if (totalCell) {
        totalCell.textContent = count;
      }
    });
  }

  // Вешаем обработчик на таблицу учеников
  const studentsTable = document.querySelector('#attendance-body');
  if (studentsTable) {
    studentsTable.addEventListener('click', handleAttendanceClick);
  }

  // Вешаем обработчик на таблицу сотрудников
  const employeesTable = document.querySelector('#employees-table');
  if (employeesTable) {
    employeesTable.addEventListener('click', handleAttendanceClick);
  }

  function generateEmployeeAttendanceCells(employeeId, attendanceData) {
    return DATES_JSON.map(date => {
      const key = `${employeeId}_${date}`;
      const status = attendanceData[key] || 'absent';

      let bgClass, icon;
      if (status === 'present') {
        bgClass = 'bg-success';
        icon = '<i class="bi bi-check-lg text-white"></i>';
      } else if (status === 'excused') {
        bgClass = 'bg-warning';
        icon = '<i class="bi bi-exclamation-lg text-white"></i>';
      } else {
        bgClass = 'bg-danger';
        icon = '<i class="bi bi-x-lg text-white"></i>';
      }

      return `
            <td class="date-cell" data-date="${date}">
                <div class="attendance-cell text-center ${bgClass}" 
                    data-employee-id="${employeeId}"
                    data-date="${date}"
                    data-attendance-type="${status}">
                    ${icon}
                </div>
            </td>
        `;
    }).join('');
  }

  // Добавление сотрудника
  const employeeForm = document.getElementById('employee-form');
  if (employeeForm) {
    employeeForm.addEventListener('submit', function (e) {
      e.preventDefault();
      const employeeId = this.querySelector('select[name="employee"]').value;
      const employeeSelect = this.querySelector('select[name="employee"]');
      const selectedOption = employeeSelect.querySelector(`option[value="${employeeId}"]`);

      // Проверка, что сотрудник не добавлен
      if (document.getElementById(`employee-${employeeId}`)) {
        showToast('Этот сотрудник уже добавлен в смену', 'warning');
        return;
      }

      const formData = new FormData(this);
      formData.append('action', 'add_employee');

      fetch(`/schedule/${SCHEDULE_ID}/`, {
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
            const tableBody = document.getElementById('employees-table');
            const emptyRow = tableBody.querySelector('tr td[colspan]');
            if (emptyRow) emptyRow.closest('tr').remove();

            // Генерируем ячейки посещаемости на основе данных с сервера
            const attendanceCells = generateEmployeeAttendanceCells(
              data.employee.id,
              data.employee.attendance
            );

            const rowCount = tableBody.querySelectorAll('tr:not([style*="display: none"])').length;
            const rowNumber = rowCount + 1;

            const newRow = document.createElement('tr');
            newRow.id = `employee-${data.employee.id}`;
            newRow.innerHTML = `
                    <td>${rowNumber}</td>
                    <td>
                        <button class="btn p-0 border-0 bg-transparent icon-btn remove-employee"
                                data-employee-id="${data.employee.id}"
                                data-employee-display="${data.employee.full_name} (${data.employee.position})" 
                                data-schedule-id="${SCHEDULE_ID}">
                            <i class="bi bi-trash text-danger fs-5"></i>
                        </button>
                    </td>
                    <td>${data.employee.full_name}</td>
                    <td>${data.employee.position}</td>
                    <td>${data.employee.rate_per_day}</td>
                    <td class="text-center">${data.employee.total_attendance}</td>
                    ${attendanceCells}
                `;
            tableBody.appendChild(newRow);
            updateEmployeeRowNumbers();

            if (selectedOption) {
              selectedOption.remove();
            }

            this.reset();
            showToast('Сотрудник успешно добавлен', 'success');
            updateAttendanceTotals(); // Обновляем итоги
          } else {
            showToast(data.error || 'Ошибка добавления сотрудника', 'error');
          }
        })
        .catch(error => {
          console.error('Error:', error);
          showToast('Произошла ошибка при добавлении сотрудника', 'error');
        });
    });
  }

  // Обработчик для формы добавления ученика
  document.addEventListener('submit', function (e) {
    if (e.target.id === 'student-form-attendance') {
      e.preventDefault();
      const form = e.target;
      const studentId = form.querySelector('select[name="student"]').value;
      const studentSelect = form.querySelector('select[name="student"]');
      const selectedOption = studentSelect.querySelector(`option[value="${studentId}"]`);

      if (!studentId) {
        showToast('Выберите ученика', 'error');
        return;
      }

      const formData = new FormData();
      formData.append('action', 'add_student');
      formData.append('student', studentId);

      fetch(`/schedule/${SCHEDULE_ID}/`, {
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
            showToast('Ученик успешно добавлен в смену', 'success');
            updateAttendanceTotals();
            setTimeout(() => {
              window.location.reload();
            }, 1000);
          } else {
            showToast(data.error || 'Ошибка добавления ученика', 'error');
          }
        })
        .catch(error => {
          console.error('Error:', error);
          showToast('Произошла ошибка при добавлении ученика', 'error');
        });
    }
  });

  // Удаление сотрудника
  document.addEventListener('click', function (e) {
    const removeBtn = e.target.closest('.remove-employee');
    if (removeBtn) {
      const employeeId = removeBtn.dataset.employeeId;
      const employeeDisplay = removeBtn.dataset.employeeDisplay;
      const scheduleId = removeBtn.dataset.scheduleId;

      if (confirm('Удалить сотрудника из смены?')) {
        fetch(`/schedule/${scheduleId}/remove_employee/${employeeId}/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN
          }
        })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              document.getElementById(`employee-${employeeId}`).remove();
              updateEmployeeRowNumbers();

              const tableBody = document.getElementById('employees-table');
              if (tableBody.querySelectorAll('tr').length === 0) {
                const emptyRow = document.createElement('tr');
                emptyRow.innerHTML = '<td colspan="4" class="text-center">Нет сотрудников</td>';
                tableBody.appendChild(emptyRow);
              }

              const select = document.querySelector('#employee-form select[name="employee"]');

              // Проверяем, существует ли уже такой option
              const optionExists = Array.from(select.options).some(opt => opt.value === employeeId);

              if (!optionExists) {
                const option = document.createElement('option');
                option.value = employeeId;
                option.textContent = employeeDisplay;
                select.appendChild(option);

                // Сортируем опции по тексту
                const options = Array.from(select.options);
                options.sort((a, b) => a.text.localeCompare(b.text));

                select.innerHTML = '';
                options.forEach(opt => select.appendChild(opt));
              }

              showToast('Сотрудник удален из смены', 'success');
              updateAttendanceTotals(); // Обновляем итоги
            }
          })
          .catch(error => {
            console.error('Error:', error);
            showToast('Произошла ошибка при удалении сотрудника', 'error');
          });
      }
    }
  });

  // Удаление ученика
  document.addEventListener('click', function (e) {
    const removeBtn = e.target.closest('.remove-student-attendance');
    if (removeBtn) {
      const studentId = removeBtn.dataset.studentId;
      const studentName = removeBtn.dataset.studentName;

      if (confirm('Удалить ученика из смены?')) {
        fetch(`/schedule/${SCHEDULE_ID}/remove_student/${studentId}/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN
          }
        })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              document.querySelector(`tr[data-student-id="${studentId}"]`).remove();
              updateStudentRowNumbers();

              // Добавляем ученика обратно в выпадающий список
              const select = document.getElementById('student-select');

              // Проверяем, не существует ли уже такого option
              const optionExists = Array.from(select.options).some(option => option.value === studentId);

              if (!optionExists) {
                const option = document.createElement('option');
                option.value = studentId;
                option.textContent = studentName;
                select.appendChild(option);

                // Сортируем варианты
                const options = Array.from(select.options);
                options.sort((a, b) => a.text.localeCompare(b.text, 'ru'));
                select.innerHTML = '';
                options.forEach(opt => select.appendChild(opt));
              }

              showToast('Ученик удален из смены', 'success');
              updateAttendanceTotals(); // Обновляем итоги
            }
          })
          .catch(error => {
            console.error('Error:', error);
            showToast('Произошла ошибка при удалении ученика', 'error');
          });
      }
    }
  });

  // Обработчик для кнопки создания ученика
  document.getElementById('create-student-btn')?.addEventListener('click', function () {
    const modal = new bootstrap.Modal(document.getElementById('createStudentModal'));
    modal.show();
  });

  // Обработчик для кнопки сохранения нового ученика
  document.getElementById('save-student-btn')?.addEventListener('click', function () {
    const btn = this;
    const originalText = btn.innerHTML;

    // Показываем индикатор загрузки
    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Сохранение...';
    btn.disabled = true;

    const full_name = document.getElementById('full_name').value;
    const phone = document.getElementById('phone').value;
    const parent_name = document.getElementById('parent_name').value;
    const attendance_type = document.getElementById('attendance_type').value;
    const default_price = document.getElementById('default_price').value;

    if (!full_name) {
      showToast('ФИО ученика обязательно', 'error');
      btn.innerHTML = originalText;
      btn.disabled = false;
      return;
    }

    fetch('/students/create/ajax/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': CSRF_TOKEN
      },
      body: JSON.stringify({
        full_name: full_name,
        phone: phone,
        parent_name: parent_name,
        attendance_type: attendance_type,
        default_price: default_price
      })
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Закрываем модальное окно
          const modal = bootstrap.Modal.getInstance(document.getElementById('createStudentModal'));
          modal.hide();

          // Добавляем нового ученика в выпадающий список
          const select = document.getElementById('student-select');
          const option = document.createElement('option');
          option.value = data.student.id;
          option.textContent = data.student.full_name;
          select.appendChild(option);

          // Автоматически выбираем нового ученика
          select.value = data.student.id;

          // Очищаем форму
          document.getElementById('full_name').value = '';
          document.getElementById('phone').value = '';
          document.getElementById('parent_name').value = '';
          document.getElementById('default_price').value = '11400';

          // Триггерим событие изменения селекта
          const event = new Event('change');
          select.dispatchEvent(event);

          showToast('Ученик успешно создан', 'success');
        } else {
          // Парсим ошибки
          let errorMsg = 'Ошибка при создании ученика';
          try {
            const errors = JSON.parse(data.error);
            errorMsg += ': ' + Object.values(errors).join(', ');
          } catch {
            errorMsg += ': ' + data.error;
          }
          showToast(errorMsg, 'error');
        }

        // Восстанавливаем кнопку
        btn.innerHTML = originalText;
        btn.disabled = false;
      })
      .catch(error => {
        console.error('Error:', error);
        showToast('Произошла ошибка при создании ученика', 'error');
        // Восстанавливаем кнопку
        btn.innerHTML = originalText;
        btn.disabled = false;
      });
  });

  // Фильтрация таблицы посещаемости
  const filterInputs = [
    'attendance-student-filter',
    'attendance-type-filter'
  ];

  filterInputs.forEach(id => {
    const element = document.getElementById(id);
    if (element) {
      element.addEventListener('input', filterAttendanceTable);
    }
  });

  // Сортировка таблицы посещаемости
  const attendanceSort = document.getElementById('attendance-sort');
  if (attendanceSort) {
    attendanceSort.addEventListener('change', function () {
      const value = this.value;
      let sortConfig = { column: 'name', direction: 1 };

      switch (value) {
        case 'name-asc': sortConfig = { column: 'name', direction: 1 }; break;
        case 'name-desc': sortConfig = { column: 'name', direction: -1 }; break;
        case 'visits-asc': sortConfig = { column: 'visits', direction: 1 }; break;
        case 'visits-desc': sortConfig = { column: 'visits', direction: -1 }; break;
      }

      sortAttendanceTable(sortConfig);
    });
  }

  // Сброс фильтров
  const resetFiltersBtn = document.getElementById('reset-attendance-filters');
  if (resetFiltersBtn) {
    resetFiltersBtn.addEventListener('click', function () {
      document.getElementById('attendance-student-filter').value = '';
      document.getElementById('attendance-type-filter').value = '';
      filterAttendanceTable();
    });
  }

  // Функция фильтрации таблицы посещаемости
  function filterAttendanceTable() {
    const studentFilter = document.getElementById('attendance-student-filter')?.value.toLowerCase() || '';
    const typeFilter = document.getElementById('attendance-type-filter')?.value || '';

    document.querySelectorAll('#attendance-body tr').forEach(row => {
      const studentName = row.querySelector('.student-column')?.textContent.toLowerCase() || '';
      const nameMatch = studentName.includes(studentFilter);

      let typeMatch = true;
      if (typeFilter) {
        typeMatch = row.dataset.attendanceType === typeFilter;
      }
      row.style.display = (nameMatch && typeMatch) ? '' : 'none';
    });
  }

  // Функция сортировки таблицы посещаемости
  function sortAttendanceTable(sortConfig) {
    const tableBody = document.getElementById('attendance-body');
    if (!tableBody) return;

    const rows = Array.from(tableBody.querySelectorAll('tr'));

    rows.sort((a, b) => {
      let valueA, valueB;

      switch (sortConfig.column) {
        case 'name':
          valueA = a.querySelector('.student-column')?.textContent || '';
          valueB = b.querySelector('.student-column')?.textContent || '';
          return valueA.localeCompare(valueB) * sortConfig.direction;

        case 'visits':
          valueA = parseInt(a.dataset.visits || '0');
          valueB = parseInt(b.dataset.visits || '0');
          return (valueA - valueB) * sortConfig.direction;
      }

      return 0;
    });

    // Удаление текущих строк
    while (tableBody.firstChild) {
      tableBody.removeChild(tableBody.firstChild);
    }

    // Добавление отсортированных строк
    rows.forEach((row, index) => {
      const firstTd = row.querySelector('td:first-child');
      if (firstTd) {
        firstTd.textContent = index + 1;
      }
      tableBody.appendChild(row);
    });
    updateStudentRowNumbers();
  }

  // Обработчики для открытия форм редактирования по клику на строке

  // Для сотрудников
  document.getElementById('employees-table').addEventListener('click', function (e) {
    const row = e.target.closest('tr[id^="employee-"]');
    if (!row) return;

    // Игнорируем клики на кнопке удаления и ячейках посещаемости
    if (e.target.closest('.remove-employee') || e.target.closest('.attendance-cell')) {
      return;
    }

    const employeeId = row.id.split('-')[1];
    loadFormIntoModal(`/employees/${employeeId}/quick_edit/`);
  });

  // Для учеников
  document.querySelectorAll('#attendance-body tr[data-student-id]').forEach(row => {
    row.addEventListener('click', function (e) {
      // Игнорируем клики на ячейках посещения и кнопке удаления
      const ignoredElements = [
        '.attendance-cell',
        '.remove-student-attendance',
        '.student-payment-btn',
        '.bi-cash' // Иконка внутри кнопки
      ];
      let shouldIgnore = false;
      for (const selector of ignoredElements) {
        if (e.target.closest(selector)) {
          shouldIgnore = true;
          break;
        }
      }
      if (shouldIgnore) return;
      const studentId = this.dataset.studentId;
      loadFormIntoModal(`/students/${studentId}/quick_edit/`);
    });
  });

  // Обработчик отправки формы платежа
  document.addEventListener('submit', function (e) {
    if (e.target.id === 'payment-form') {
      e.preventDefault();
      const form = e.target;
      const formData = new FormData(form);

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
            showToast('Платеж успешно создан', 'success');

            // Закрываем модальное окно
            const modal = bootstrap.Modal.getInstance(document.getElementById('paymentModal'));
            modal.hide();

            // Обновляем данные на странице
            updateStudentPaymentData(data.student_id, data.schedule_id, data.payment_amount, parseFloat(data.total_paid));

            // Обновляем кнопку платежа
            const paymentBtn = document.querySelector(`.student-payment-btn[data-student-id="${data.student_id}"]`);
            if (paymentBtn) {
              const icon = paymentBtn.querySelector('i');
              icon.classList.remove('text-success');
              icon.classList.add('text-primary');
            }
            // Принудительно обновляем итоги
            updateTotalPayments();
            updateFinanceSummary();
          } else {
            if (data.errors) {
              let errorMsg = 'Ошибки в форме: ';
              for (const field in data.errors) {
                errorMsg += data.errors[field].join(', ');
              }
              showToast(errorMsg, 'error');
            } else {
              showToast(data.error || 'Ошибка при создании платежа', 'error');
            }
          }
        })
        .catch(error => {
          console.error('Error:', error);
          showToast('Произошла ошибка при создании платежа', 'error');
        });
    }
  });

  // Функция обновления данных о платежах студента
  function updateStudentPaymentData(studentId, scheduleId, paymentAmount, totalPaid) {
    const row = document.querySelector(`tr[data-student-id="${studentId}"]`);
    if (row) {
      // Обновляем ячейку с платежами
      const paymentCell = row.cells[3];
      paymentCell.textContent = totalPaid > 0 ? totalPaid.toFixed(2) : '—';

      // Обновляем цвет ячейки
      const costCell = row.cells[2];
      const cost = parseFloat(costCell.textContent) || 0;

      if (totalPaid >= cost) {
        paymentCell.classList.add('payment-success');
        paymentCell.classList.remove('payment-danger');
      } else {
        paymentCell.classList.add('payment-danger');
        paymentCell.classList.remove('payment-success');
      }

      // Обновляем итоговую сумму платежей
      updateTotalPayments();
      updateFinanceSummary();
    }
  }

  // Функция обновления итоговой суммы платежей
  function updateTotalPayments() {
    let total = 0;
    document.querySelectorAll('#attendance-body tr[data-student-id]').forEach(row => {
      const paymentCell = row.cells[3];
      const paymentText = paymentCell.textContent.trim();

      // Пропускаем ячейки с прочерком
      if (paymentText === '—') {
        return;
      }

      const paymentAmount = parseFloat(paymentText.replace(/[^\d,.]/g, '').replace(',', '.')) || 0;
      total += paymentAmount;
    });

    // Форматируем число с разделителем тысяч и двумя знаками после запятой
    const formatter = new Intl.NumberFormat('ru-RU', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
    const formattedTotal = formatter.format(total);

    // Обновляем элемент с итогом платежей
    const totalPaymentsElement = document.getElementById('total-payments-cell');
    if (totalPaymentsElement) {
      totalPaymentsElement.textContent = formattedTotal;
    }

    // Обновляем финансовую сводку
    const financeIncomeElement = document.getElementById('finance-income');
    if (financeIncomeElement) {
      financeIncomeElement.textContent = formattedTotal + ' руб.';
    }

    // Обновляем сальдо
    updateFinanceSummary();

    return total;
  }
  
  // Обработчик для кнопок удаления в модальных окнах
  document.addEventListener('click', function (e) {
    if (e.target.id === 'delete-student-btn') {
      e.preventDefault();
      handleDeleteButtonClick(e.target, 'student');
    }

    if (e.target.id === 'delete-employee-btn') {
      e.preventDefault();
      handleDeleteButtonClick(e.target, 'employee');
    }
  });

  // Обновление данных сотрудника на странице
  function updateEmployeeRow(employee) {
    const row = document.getElementById(`employee-${employee.id}`);
    if (row) {
      row.cells[2].textContent = employee.full_name;
      row.cells[3].textContent = employee.position_display;
      row.cells[4].textContent = `${employee.rate_per_day}`;

      // Обновляем данные в кнопке удаления
      const removeBtn = row.querySelector('.remove-employee');
      if (removeBtn) {
        removeBtn.dataset.employeeDisplay = `${employee.full_name} (${employee.position_display})`;
      }
    }
  }

  // Обновление данных ученика на странице
  function updateStudentRow(student) {
    const row = document.querySelector(`tr[data-student-id="${student.id}"]`);
    if (row) {
      row.cells[2].textContent = student.individual_price || student.default_price;
      row.cells[4].textContent = student.attendance_type_display;
      row.cells[5].textContent = student.full_name;

      // Обновляем данные в кнопке удаления
      const removeBtn = row.querySelector('.remove-student-attendance');
      if (removeBtn) {
        removeBtn.dataset.studentName = student.full_name;
      }
    }
  }

  // Общая функция обработки отправки форм
  function handleQuickFormSubmit(form, entityName) {
    const formData = new FormData(form);
    const originalButton = form.querySelector('button[type="submit"]');
    const originalButtonText = originalButton.innerHTML;

    // Показываем индикатор загрузки
    originalButton.disabled = true;
    originalButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Сохранение...';

    fetch(form.action, {
      method: form.method,
      body: formData,
      headers: {
        'X-CSRFToken': CSRF_TOKEN,
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Получаем экземпляр модального окна и закрываем его
          const modalElement = document.getElementById('universalFormModal');

          // Используем более надежный способ закрытия модального окна
          if (modalElement) {
            // Получаем экземпляр модального окна, если он существует
            const modalInstance = bootstrap.Modal.getInstance(modalElement);

            if (modalInstance) {
              modalInstance.hide();
            } else {
              // Если экземпляр не найден, создаем новый и сразу закрываем
              const newModalInstance = new bootstrap.Modal(modalElement);
              newModalInstance.hide();
            }

            // Удаляем backdrop (затемнение) вручную, если он остался
            setTimeout(() => {
              const backdrops = document.querySelectorAll('.modal-backdrop');
              backdrops.forEach(backdrop => {
                backdrop.remove();
              });

              // Восстанавливаем прокрутку страницы более надежно
              document.body.classList.remove('modal-open');
              document.body.style.overflow = '';
              document.body.style.paddingRight = '';

              // Принудительно восстанавливаем возможность прокрутки
              document.documentElement.style.overflow = '';
              document.documentElement.style.paddingRight = '';

              // Добавляем небольшой таймаут для полного восстановления
              setTimeout(() => {
                // Принудительно активируем прокрутку
                window.dispatchEvent(new Event('scroll'));

                // Принудительно восстанавливаем фокус и взаимодействие
                document.body.focus();
                document.body.click();

                // Восстанавливаем стандартное поведение прокрутки
                document.body.style.overflow = 'auto';
                document.body.style.overflowX = 'hidden';
                document.documentElement.style.overflow = 'auto';
                document.documentElement.style.overflowX = 'hidden';
              }, 50);
            }, 100);
          }

          showToast(`${entityName} успешно сохранен`, 'success');

          if (form.id === 'student-quick-edit-form' && data.student) {
            updateStudentRow(data.student);
          }
          else if (form.id === 'employee-quick-edit-form' && data.employee) {
            updateEmployeeRow(data.employee);
          }
        } else {
          let errorMsg = 'Ошибка сохранения: ';
          if (data.errors) {
            for (let field in data.errors) {
              errorMsg += data.errors[field].join(', ');
            }
          } else {
            errorMsg += 'Неизвестная ошибка';
          }
          showToast(errorMsg, 'error');
        }
      })
      .catch(error => {
        console.error('Error:', error);
        showToast('Произошла ошибка при сохранении', 'error');
      })
      .finally(() => {
        // Восстанавливаем кнопку
        originalButton.disabled = false;
        originalButton.innerHTML = originalButtonText;
      });
  }

  // Общая функция обработки кнопок удаления
  function handleDeleteButtonClick(button, entityType) {
    const entityId = button.dataset[`${entityType}Id`];
    const url = `/${entityType === 'student' ? 'students' : 'employees'}/delete/${entityId}/`;

    fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': CSRF_TOKEN,
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
      .then(response => {
        if (response.ok) {
          return response.json();
        }
        throw new Error('Network response was not ok');
      })
      .then(data => {
        if (data.success) {
          const modal = bootstrap.Modal.getInstance(
            document.getElementById('universalFormModal')
          );
          modal.hide();
          showToast(`${entityType === 'student' ? 'Ученик' : 'Сотрудник'} успешно удален`, 'success');
          setTimeout(() => window.location.reload(), 1000);
        }
      })
      .catch(error => {
        console.error('Error:', error);
        showToast('Произошла ошибка при удалении', 'error');
      });
  }

  document.getElementById('create-employee-btn')?.addEventListener('click', function () {
    const modal = new bootstrap.Modal(document.getElementById('createEmployeeModal'));
    modal.show();
  });

  // Обработчик для кнопки сохранения нового сотрудника
  document.getElementById('save-employee-btn')?.addEventListener('click', function () {
    const btn = this;
    const originalText = btn.innerHTML;

    btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Сохранение...';
    btn.disabled = true;

    const full_name = document.getElementById('employee_full_name').value;
    const position = document.getElementById('position').value;
    const rate_per_day = document.getElementById('rate_per_day').value;

    if (!full_name) {
      showToast('ФИО сотрудника обязательно', 'error');
      btn.innerHTML = originalText;
      btn.disabled = false;
      return;
    }

    fetch('/employees/create/ajax/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': CSRF_TOKEN
      },
      body: JSON.stringify({
        full_name: full_name,
        position: position,
        rate_per_day: rate_per_day
      })
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          const modal = bootstrap.Modal.getInstance(document.getElementById('createEmployeeModal'));
          modal.hide();

          // Обновляем выпадающий список
          const select = document.querySelector('#employee-form select[name="employee"]');
          const option = document.createElement('option');
          option.value = data.employee.id;
          option.textContent = `${data.employee.full_name} (${data.employee.get_position_display})`;
          select.appendChild(option);

          // Автоматически выбираем нового сотрудника
          select.value = data.employee.id;

          showToast('Сотрудник успешно создан', 'success');
        } else {
          showToast(data.error || 'Ошибка при создании сотрудника', 'error');
        }
        btn.innerHTML = originalText;
        btn.disabled = false;
      })
      .catch(error => {
        console.error('Error:', error);
        showToast('Произошла ошибка при создании сотрудника', 'error');
        btn.innerHTML = originalText;
        btn.disabled = false;
      });
  });

  // Функция для обновления итоговой суммы расходов
  function updateExpensesTotal() {
    let total = 0;
    // Собираем все строки расходов
    document.querySelectorAll('#expenses-table-body tr[data-expense-id]').forEach(row => {
      // Сумма находится в последней ячейке (индекс 4)
      const amountCell = row.cells[4];
      const amountText = amountCell.textContent.trim();
      // Парсим число, удаляя все нечисловые символы
      const amount = parseFloat(amountText.replace(/[^\d,.]/g, '').replace(',', '.')) || 0;
      total += amount;
    });

    // Форматируем число с разделителем тысяч и двумя знаками после запятой
    const formatter = new Intl.NumberFormat('ru-RU', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
    const formattedTotal = formatter.format(total);

    // Обновляем элемент с итогом в таблице расходов
    const totalExpenseCell = document.querySelector('#expenses-table-body + tfoot .total-summary-row td:last-child');
    if (totalExpenseCell) {
      totalExpenseCell.textContent = formattedTotal + ' руб.';
    }

    // Обновляем элемент в финансовой сводке
    const financeExpenseElement = document.getElementById('finance-expense');
    if (financeExpenseElement) {
      financeExpenseElement.textContent = formattedTotal + ' руб.';
    }

    return total;
  }

  // Функция для обновления нумерации строк в таблице расходов
  function updateExpenseRowNumbers() {
    const tableBody = document.getElementById('expenses-table-body');
    const rows = tableBody.querySelectorAll('tr:not([style*="display: none"])');

    rows.forEach((row, index) => {
      // Пропускаем строку "Нет расходов"
      if (!row.querySelector('td[colspan]')) {
        const numberCell = row.querySelector('td:first-child');
        if (numberCell) {
          numberCell.textContent = index + 1;
        }
      }
    });
  }

  // Кнопка добавления расхода
  document.getElementById('add-expense-btn')?.addEventListener('click', function () {
    loadExpenseForm(`/payroll/expenses/create/?schedule=${SCHEDULE_ID}`);
  });

  // Обработчик кликов по строкам расходов
  document.addEventListener('click', function (e) {
    const row = e.target.closest('tr.clickable-expense-row');
    if (row && !e.target.closest('.delete-expense-btn')) {
      const expenseId = row.dataset.expenseId;
      loadExpenseForm(`/payroll/expenses/edit/${expenseId}/`);
    }
  });

  // Кнопки удаления расхода
  document.addEventListener('click', function (e) {
    // Обработка кнопок удаления расходов
    const deleteBtn = e.target.closest('.delete-expense-btn');
    if (deleteBtn) {
      const expenseId = deleteBtn.dataset.expenseId;
      if (confirm('Удалить этот расход?')) {
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
              const row = document.querySelector(`tr[data-expense-id="${expenseId}"]`);
              if (row) row.remove();

              // Обновляем таблицу если нет расходов
              if (!document.querySelector('#expenses-table-body tr')) {
                document.getElementById('expenses-table-body').innerHTML =
                  '<tr><td colspan="5" class="text-center">Нет расходов</td></tr>';
              } else {
                // Обновляем нумерацию только если есть строки
                updateExpenseRowNumbers();
              }
              showToast('Расход успешно удален', 'success');
              updateFinanceSummary()
              updateExpensesTotal(); // Обновляем сумму
              document.dispatchEvent(new CustomEvent('expenseUpdated'));
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
              <td>${expenseRow.querySelector('td:first-child').textContent}</td>
              <td>
                  <button class="btn p-0 border-0 bg-transparent icon-btn delete-expense-btn"
                          data-expense-id="${data.expense.id}">
                      <i class="bi bi-trash text-danger fs-5"></i>
                  </button>
              </td>
              <td>${data.expense.category_display}</td>
              <td>${data.expense.comment || ''}</td>
              <td>${data.expense.amount} руб.</td>
            `;
              updateFinanceSummary(); // Добавляем обновление сальдо
              document.dispatchEvent(new CustomEvent('expenseUpdated'));
            } else {
              // Добавляем новую строку
              const emptyRow = tableBody.querySelector('tr td[colspan]');
              if (emptyRow) {
                emptyRow.closest('tr').remove();
              }

              const newRow = document.createElement('tr');
              newRow.dataset.expenseId = data.expense.id;
              newRow.className = 'clickable-expense-row';
              newRow.innerHTML = `
              <td></td> <!-- Пустая ячейка для номера -->
              <td>
                  <button class="btn p-0 border-0 bg-transparent icon-btn delete-expense-btn"
                          data-expense-id="${data.expense.id}">
                      <i class="bi bi-trash text-danger fs-5"></i>
                  </button>
              </td>
              <td>${data.expense.category_display}</td>
              <td>${data.expense.comment || ''}</td>
              <td>${data.expense.amount} руб.</td>
            `;
              tableBody.appendChild(newRow);

              // Обновляем нумерацию после добавления
              updateExpenseRowNumbers();
            }

            showToast('Расход успешно сохранен', 'success');
            updateFinanceSummary();
            updateExpensesTotal();
            document.dispatchEvent(new Event('expenseUpdated'));
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

  // Обновить обработчик кликов по строкам учеников (игнорировать кнопки платежей)
  document.querySelectorAll('#attendance-body tr[data-student-id]').forEach(row => {
    row.addEventListener('click', function (e) {
      // Игнорируем клики на:
      // - ячейках посещения
      // - кнопке удаления
      // - кнопке платежа
      if (e.target.closest('.attendance-cell') ||
        e.target.closest('.remove-student-attendance') ||
        e.target.closest('.student-payment-btn')) {
        return;
      }
      const studentId = this.dataset.studentId;
      loadFormIntoModal(`/students/${studentId}/quick_edit/`);
    });
  });

  // Обработчик для кнопки платежа
  document.addEventListener('click', function (e) {
    const paymentBtn = e.target.closest('.student-payment-btn');
    if (paymentBtn) {
      e.preventDefault();
      e.stopPropagation();
      const studentId = paymentBtn.dataset.studentId;
      const scheduleId = paymentBtn.dataset.scheduleId;

      // Загружаем форму платежа
      loadPaymentForm(`/students/${studentId}/payments/add_payment_form/?schedule_id=${scheduleId}`);
    }
  });


  // Инициализируем баланс при загрузке формы
  document.addEventListener('DOMContentLoaded', function () {
    const paymentModal = document.getElementById('paymentModal');
    if (paymentModal) {
      paymentModal.addEventListener('shown.bs.modal', function () {
        updatePaymentFormBalance();
      });
    }
  });

  // Функция для обновления финансовой сводки
  function updateFinanceSummary() {
    // Получаем значения расходов и доходов
    const expenseElement = document.getElementById('finance-expense');
    const incomeElement = document.getElementById('finance-income');

    // Извлекаем только числовые значения (удаляем " руб." и другие нечисловые символы)
    const expense = parseFloat(
      expenseElement.textContent.replace(/[^\d,.]/g, '').replace(',', '.')
    ) || 0;

    const income = parseFloat(
      incomeElement.textContent.replace(/[^\d,.]/g, '').replace(',', '.')
    ) || 0;

    // Рассчитываем сальдо
    const balance = income - expense;

    // Форматируем числа с разделителями тысяч и двумя знаками после запятой
    const formatter = new Intl.NumberFormat('ru-RU', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });

    // Обновляем отображение сальдо
    const balanceCell = document.getElementById('finance-balance');
    balanceCell.textContent = formatter.format(balance) + ' руб.';

    // Добавляем цвет в зависимости от результата
    balanceCell.classList.remove('text-success', 'text-danger');
    if (balance > 0) {
      balanceCell.classList.add('text-success');
    } else if (balance < 0) {
      balanceCell.classList.add('text-danger');
    }

    return balance;
  }

  function colorizePaymentCells() {
    const rows = document.querySelectorAll('#attendance-body tr[data-student-id]');

    rows.forEach(row => {
      const costCell = row.cells[2]; // Ячейка стоимости
      const paymentCell = row.cells[3]; // Ячейка платежей

      // Получаем числовые значения
      const cost = parseFloat(costCell.textContent) || 0;
      const paymentText = paymentCell.textContent.trim();
      const payment = paymentText === '—' ? 0 : parseFloat(paymentText) || 0;

      // Применяем классы в зависимости от условия
      if (payment >= cost) {
        paymentCell.classList.add('payment-success');
        paymentCell.classList.remove('payment-danger');
      } else {
        paymentCell.classList.add('payment-danger');
        paymentCell.classList.remove('payment-success');
      }
    });
  }

  // Функция для обновления текста кнопок при загрузке страницы
  function updatePaymentButtonsText() {
    document.querySelectorAll('.student-payment-btn').forEach(btn => {
      const studentId = btn.dataset.studentId;
      const scheduleId = btn.dataset.scheduleId;

      // Можно добавить запрос к серверу для получения информации о платежах
      // или использовать данные, которые уже есть на странице
      const paymentCell = document.querySelector(`tr[data-student-id="${studentId}"] td:nth-child(4)`);
      if (paymentCell && paymentCell.textContent.trim() !== '—') {
        const icon = btn.querySelector('i');
        icon.classList.remove('text-success');
        icon.classList.add('text-primary');
      }
    });
  }



  // Обновляем доступный баланс при изменении суммы
  document.addEventListener('input', function (e) {
    if (e.target.name === 'amount') {
      updatePaymentFormBalance();
    }
  });

  updateExpensesTotal();
  // Обновляем финансовую сводку
  updateFinanceSummary();
  // Инициализация итогов при загрузке страницы
  updateAttendanceTotals();
  // Обновляем сводку при изменениях
  document.addEventListener('expenseUpdated', updateFinanceSummary);
  document.addEventListener('paymentUpdated', updateFinanceSummary);

  // Инициализация при загрузке страницы
  document.addEventListener('DOMContentLoaded', function () {
    // Обновляем финансовую сводку
    updateFinanceSummary();

    // Обновляем цвет ячеек платежей
    colorizePaymentCells();

    // Обновляем итоговую сумму платежей
    updateTotalPayments();

    // Обновляем текст кнопок платежей
    updatePaymentButtonsText();

    console.log('Schedule detail initialization complete');
  });
});