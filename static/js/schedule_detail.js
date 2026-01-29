document.addEventListener('DOMContentLoaded', function () {
  colorizePaymentCells();
  setupStudentSearch();

  // Функция для добавления ученика обратно в datalist
  function addStudentToDatalist(studentId, studentName) {
    const datalist = document.getElementById('students-datalist');

    // Проверяем, нет ли уже такого ученика в списке
    const existingOption = datalist.querySelector(`option[data-id="${studentId}"]`);
    if (!existingOption) {
      const option = document.createElement('option');
      option.value = studentName;
      option.setAttribute('data-id', studentId);
      datalist.appendChild(option);

      // Сортируем опции по алфавиту
      const options = Array.from(datalist.options);
      options.sort((a, b) => a.value.localeCompare(b.value));

      // Очищаем и перезаполняем datalist
      datalist.innerHTML = '';
      options.forEach(opt => datalist.appendChild(opt));
    }
  }

  // Функция для загрузки формы в модальное окно
  function loadFormIntoModal(url) {
    fetch(url)
      .then(response => response.text())
      .then(html => {
        document.getElementById('universalFormModalContent').innerHTML = html;
        const modal = new bootstrap.Modal(document.getElementById('universalFormModal'));
        modal.show();

        // Добавляем обработчик для формы
        const form = document.querySelector('#universalFormModal form');
        if (form) {
          form.addEventListener('submit', function (e) {
            e.preventDefault();
            let entityName = '';
            if (form.id === 'student-quick-edit-form') {
              entityName = 'Ученик';
            } else if (form.id === 'employee-quick-edit-form') {
              entityName = 'Сотрудник';
            }
            handleQuickFormSubmit(form, entityName);
          });
        }
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
            `${data.balance.toLocaleString('ru-RU')}`;
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
                const countCell = row.querySelector('td:nth-child(7)'); // Обновлен индекс из-за нового столбца
                if (countCell) {
                  countCell.textContent = data.total_attendance;
                }

                // Обновляем зарплату сотрудника
                updateEmployeeSalary(data.employee_id, data.total_attendance);
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

  // Функция обновления зарплаты сотрудника
  function updateEmployeeSalary(employeeId, attendanceCount) {
    const row = document.getElementById(`employee-${employeeId}`);
    if (!row) return;

    const rateCell = row.querySelector('td:nth-child(6)'); // Ставка
    const salaryCell = row.querySelector('td:nth-child(5)'); // Начисленная зарплата

    if (rateCell && salaryCell) {
      const rate = parseFloat(normalizeDecimal(rateCell.textContent)) || 0;
      const salary = rate * attendanceCount;

      // Проверяем, не выплачена ли уже зарплата
      const isAlreadyPaid = salaryCell.querySelector('.text-success');

      if (!isAlreadyPaid) {
        salaryCell.textContent = salary.toFixed(2);

        // Обновляем data-атрибут для кнопки выплаты
        const payBtn = row.querySelector('.pay-salary-btn');
        if (payBtn) {
          payBtn.dataset.salaryAmount = salary.toFixed(2);
        }
      }
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

    const countCell = row.querySelector('td:nth-child(8)'); // Обновлен индекс
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
                        <button class="btn p-0 border-0 bg-transparent icon-btn pay-salary-btn"
                                data-employee-id="${data.employee.id}"
                                data-employee-name="${data.employee.full_name}"
                                data-salary-amount="${data.employee.calculated_salary || 0}"
                                data-schedule-id="${SCHEDULE_ID}"
                                data-bs-toggle="tooltip" title="Выплатить зарплату">
                            <i class="bi bi-cash-coin text-success fs-5"></i>
                        </button>
                        <button class="btn p-0 border-0 bg-transparent icon-btn remove-employee"
                                data-employee-id="${data.employee.id}"
                                data-employee-display="${data.employee.full_name} (${data.employee.position_display || data.employee.position_name})"
 
                                data-schedule-id="${SCHEDULE_ID}">
                            <i class="bi bi-trash text-danger fs-5"></i>
                        </button>
                    </td>
                    <td>${data.employee.full_name}</td>
                    <td>${data.employee.position_display || data.employee.position_name}</td>
                    <td class="salary-amount">${data.employee.calculated_salary || 0}</td>
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
      const studentId = document.getElementById('student-id-input').value;
      const studentName = document.getElementById('student-search-input').value;

      if (!studentId) {
        showToast('Выберите ученика из списка', 'error');
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
            // УДАЛЯЕМ УЧЕНИКА ИЗ DATALIST ПРИ УСПЕШНОМ ДОБАВЛЕНИИ
            removeStudentFromDatalist(studentId);

            showToast('Ученик успешно добавлен в смену. Списано ' + data.student.price, 'success');
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

  // Функция для удаления ученика из datalist
  function removeStudentFromDatalist(studentId) {
    const datalist = document.getElementById('students-datalist');
    const optionToRemove = datalist.querySelector(`option[data-id="${studentId}"]`);
    if (optionToRemove) {
      optionToRemove.remove();
    }
  }

  // Функция для добавления сотрудника обратно в select
  function addEmployeeToSelect(employeeId, employeeDisplay) {
    const select = document.querySelector('#employee-form select[name="employee"]');

    // Проверяем, нет ли уже такого сотрудника в списке
    const existingOption = select.querySelector(`option[value="${employeeId}"]`);
    if (!existingOption) {
      const option = document.createElement('option');
      option.value = employeeId;
      option.textContent = employeeDisplay;
      select.appendChild(option);

      // Сортируем опции по алфавиту
      const options = Array.from(select.options);
      options.sort((a, b) => a.textContent.localeCompare(b.textContent));

      // Очищаем и перезаполняем select
      select.innerHTML = '<option value="">Выберите сотрудника</option>';
      options.forEach(opt => {
        if (opt.value) { // Пропускаем пустую опцию
          select.appendChild(opt);
        }
      });
    }
  }

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
              addEmployeeToSelect(employeeId, employeeDisplay);
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
      const scheduleId = removeBtn.dataset.scheduleId;

      if (confirm('Удалить ученика из смены?')) {
        fetch(`/schedule/${scheduleId}/remove_student/${studentId}/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN
          }
        })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              // Удаляем строку из DOM
              const row = document.querySelector(`tr[data-student-id="${studentId}"]`);
              if (row) row.remove();

              updateStudentRowNumbers();

              // Обновляем финансовые данные
              updateTotalPayments();
              updateFinanceSummary();
              updateAttendanceTotals();

              // ДОБАВЛЯЕМ УЧЕНИКА ОБРАТНО В DATALIST
              addStudentToDatalist(studentId, studentName);

              // Запрашиваем обновленные данные с сервера
              fetchUpdatedScheduleData(scheduleId);

              showToast('Ученик удален из смены. Списание отменено.', 'success');
            } else {
              showToast(data.error || 'Ошибка при удалении ученика', 'error');
            }
          })
          .catch(error => {
            console.error('Error:', error);
            showToast('Произошла ошибка при удалении ученика', 'error');
          });
      }
    }
  });

  // Функция для запроса обновленных данных с сервера
  function fetchUpdatedScheduleData(scheduleId) {
    fetch(`/schedule/${scheduleId}/get_updated_data/`, {
      method: 'GET',
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          // Обновляем глобальные переменные с данными
          if (data.total_payments !== undefined) {
            window.totalPayments = data.total_payments;
          }
          if (data.total_expenses !== undefined) {
            window.totalExpenses = data.total_expenses;
          }

          // Принудительно обновляем отображение
          updateTotalPayments();
          updateFinanceSummary();
          updateAttendanceTotals();
        }
      })
      .catch(error => {
        console.error('Error fetching updated data:', error);
      });
  }

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

          // Добавляем нового ученика в datalist
          const datalist = document.getElementById('students-datalist');
          const option = document.createElement('option');
          option.value = data.student.full_name;
          option.setAttribute('data-id', data.student.id);
          datalist.appendChild(option);

          // Автоматически заполняем поле поиска
          document.getElementById('student-search-input').value = data.student.full_name;
          document.getElementById('student-id-input').value = data.student.id;

          // Очищаем форму
          document.getElementById('full_name').value = '';
          document.getElementById('phone').value = '';
          document.getElementById('parent_name').value = '';
          document.getElementById('default_price').value = '11400';

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

    // Обновляем итоги платежей после фильтрации
    updateTotalPayments();
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

    // Игнорируем клики на кнопке удаления, ячейках посещаемости и кнопке выплаты зарплаты
    if (e.target.closest('.remove-employee') || e.target.closest('.attendance-cell') || e.target.closest('.pay-salary-btn')) {
      return;
    }

    const employeeId = row.id.split('-')[1];
    loadFormIntoModal(`/employees/${employeeId}/quick_edit/`);
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

  // Функция для обновления данных о платежах студента
  function updateStudentPaymentData(studentId, scheduleId, paymentAmount, totalPaid) {
    const row = document.querySelector(`tr[data-student-id="${studentId}"]`);
    if (row) {
      // Обновляем ячейку с платежами (4-я ячейка)
      const paymentCell = row.cells[3];
      paymentCell.textContent = totalPaid > 0 ? totalPaid.toFixed(2) : '—';

      // Удаляем старые классы подсветки из ячейки платежей
      paymentCell.classList.remove('payment-success', 'payment-danger');

      // Обновляем цвет ячейки платежей (старая логика - удаляем)
      const costCell = row.cells[2];
      const cost = parseFloat(costCell.textContent) || 0;

      // ОБНОВЛЯЕМ БАЛАНС (5-я ячейка) - теперь баланс = платежи - стоимость
      const balanceCell = row.cells[4];
      const newBalance = totalPaid - cost;
      balanceCell.textContent = newBalance.toFixed(2);

      // Убираем все старые классы из ячейки баланса
      balanceCell.classList.remove('text-success', 'text-danger', 'text-muted', 'balance-positive', 'balance-negative', 'balance-zero');

      // ДОБАВЛЯЕМ ПРАВИЛЬНЫЕ КЛАССЫ ПОДСВЕТКИ В ЯЧЕЙКУ БАЛАНСА
      if (newBalance > 0) {
        balanceCell.classList.add('balance-positive');
      } else if (newBalance < 0) {
        balanceCell.classList.add('balance-negative');
      } else {
        balanceCell.classList.add('balance-zero');
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
      // Пропускаем скрытые строки (например, отфильтрованные) и удаленные строки
      if (row.style.display === 'none' || !row.isConnected) {
        return;
      }

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
      financeIncomeElement.textContent = formattedTotal;
    }

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
      row.cells[3].textContent = employee.position_display || employee.position_name;
      row.cells[5].textContent = `${employee.rate_per_day}`; // Обновлен индекс

      // Обновляем данные в кнопке удаления
      const removeBtn = row.querySelector('.remove-employee');
      if (removeBtn) {
        removeBtn.dataset.employeeDisplay = `${employee.full_name} (${employee.position_display || employee.position_name})`;
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

    const formData = new FormData(document.getElementById('create-employee-form'));
    const data = Object.fromEntries(formData.entries());

    // Преобразуем пустые строки в null для необязательных полей
    if (!data.branch_id) data.branch_id = null;
    if (!data.schedule_id) data.schedule_id = null;

    fetch('/employees/create/ajax/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': CSRF_TOKEN
      },
      body: JSON.stringify(data)
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          const modal = bootstrap.Modal.getInstance(document.getElementById('createEmployeeModal'));
          modal.hide();

          // Обновляем выпадающий список сотрудников
          const select = document.querySelector('#employee-form select[name="employee"]');
          const option = document.createElement('option');
          option.value = data.employee.id;
          option.textContent = `${data.employee.full_name} (${data.employee.position_display || data.employee.position_name})`;
          select.appendChild(option);

          // Автоматически выбираем нового сотрудника
          select.value = data.employee.id;

          // Очищаем форму
          document.getElementById('create-employee-form').reset();

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

  // Функция для обновления нумерации строк в таблице финансовых операций
  function updateExpenseRowNumbers() {
    const tableBody = document.getElementById('expenses-table-body');
    const rows = tableBody.querySelectorAll('tr:not([style*="display: none"])');

    rows.forEach((row, index) => {
      // Пропускаем строку "Нет финансовых операций"
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

  // Обработчик кликов по строкам финансовых операций (только для расходов)
  document.addEventListener('click', function (e) {
    const row = e.target.closest('tr.clickable-expense-row');
    if (row && !e.target.closest('.delete-record-btn')) {
      const recordType = row.dataset.recordType;
      const recordId = row.dataset.recordId;

      // Редактирование только для расходов
      if (recordType === 'expense') {
        loadExpenseForm(`/payroll/expenses/edit/${recordId}/`);
      }
      // Для зарплат редактирование не предусмотрено, но можно добавить при необходимости
    }
  });

  // Универсальная функция удаления финансовой записи
  document.addEventListener('click', function (e) {
    const deleteBtn = e.target.closest('.delete-record-btn');
    if (deleteBtn) {
      const recordType = deleteBtn.dataset.recordType;
      const recordId = deleteBtn.dataset.recordId;

      let url, confirmMessage;

      if (recordType === 'expense') {
        url = `/payroll/expenses/delete/${recordId}/`;
        confirmMessage = 'Удалить этот расход?';
      } else if (recordType === 'salary') {
        url = `/payroll/salaries/delete/${recordId}/`;
        confirmMessage = 'Удалить запись о выплате зарплаты?';
      }

      if (confirm(confirmMessage)) {
        fetch(url, {
          method: 'POST',
          headers: {
            'X-CSRFToken': CSRF_TOKEN,
            'X-Requested-With': 'XMLHttpRequest'
          }
        })
          .then(response => response.json())
          .then(data => {
            if (data.success) {
              const row = document.querySelector(`tr[data-record-id="${recordId}"][data-record-type="${recordType}"]`);
              if (row) row.remove();

              // Обновляем таблицу если нет записей
              if (!document.querySelector('#expenses-table-body tr')) {
                document.getElementById('expenses-table-body').innerHTML =
                  '<tr><td colspan="5" class="text-center">Нет финансовых операций</td></tr>';
              } else {
                // Обновляем нумерацию только если есть строки
                updateExpenseRowNumbers();
              }
              showToast('Запись успешно удалена', 'success');
              updateFinanceSummary();
              updateExpensesTotal(); // Обновляем сумму
              document.dispatchEvent(new CustomEvent('expenseUpdated'));

              // Если удалена зарплата, обновляем отображение у сотрудника
              if (recordType === 'salary') {
                updateSalaryDisplayAfterDelete(recordId);
              }
            }
          })
          .catch(error => {
            console.error('Error:', error);
            showToast('Произошла ошибка при удалении записи', 'error');
          });
      }
    }
  });

  // Функция для обновления отображения зарплаты после удаления
  function updateSalaryDisplayAfterDelete(salaryId) {
    // Находим все кнопки выплаты зарплаты и обновляем их состояние
    document.querySelectorAll('.pay-salary-btn').forEach(btn => {
      const employeeId = btn.dataset.employeeId;
      const salaryCell = document.querySelector(`#employee-${employeeId} .salary-amount`);

      if (salaryCell) {
        // Показываем кнопку выплаты с правильными классами
        btn.classList.remove('d-none');
        btn.style.display = 'inline-block'; // Явно устанавливаем display
        btn.classList.add('btn', 'p-0', 'border-0', 'bg-transparent', 'icon-btn', 'pay-salary-btn');

        // Обновляем отображение зарплаты на рассчитанное значение
        const rate = parseFloat(document.querySelector(`#employee-${employeeId} td:nth-child(6)`).textContent) || 0;
        const attendanceCount = parseInt(document.querySelector(`#employee-${employeeId} td:nth-child(7)`).textContent) || 0;
        const calculatedSalary = rate * attendanceCount;

        salaryCell.textContent = calculatedSalary.toFixed(2);
        salaryCell.classList.remove('text-success');

        // Обновляем data-атрибут кнопки
        btn.dataset.salaryAmount = calculatedSalary.toFixed(2);
      }
    });
  }

  // Функция для обновления таблицы финансовых операций после добавления расхода
  function updateExpensesTable(expenseData) {
    const tableBody = document.getElementById('expenses-table-body');
    const emptyRow = tableBody.querySelector('tr td[colspan]');

    if (emptyRow) {
      emptyRow.closest('tr').remove();
    }

    const newRow = document.createElement('tr');
    newRow.dataset.recordType = 'expense';
    newRow.dataset.recordId = expenseData.id;
    newRow.className = 'clickable-expense-row';
    newRow.innerHTML = `
      <td></td>
      <td>
        <button class="btn p-0 border-0 bg-transparent icon-btn delete-record-btn"
                data-record-type="expense"
                data-record-id="${expenseData.id}">
          <i class="bi bi-trash text-danger fs-5"></i>
        </button>
      </td>
      <td>${expenseData.category_display || expenseData.category || ''}</td>
      <td>${expenseData.comment || ''}</td>
      <td>${expenseData.amount}</td>
    `;
    tableBody.appendChild(newRow);

    // Обновляем нумерацию
    updateExpenseRowNumbers();

    // Обновляем общую сумму расходов
    updateExpensesTotal();
  }
  
  // Функция для обновления таблицы финансовых операций после выплаты зарплаты
  function updateExpensesTableAfterSalary(recordData) {
    const tableBody = document.getElementById('expenses-table-body');
    const emptyRow = tableBody.querySelector('tr td[colspan]');

    if (emptyRow) {
      emptyRow.closest('tr').remove();
    }

    const newRow = document.createElement('tr');
    newRow.dataset.recordType = 'salary';
    newRow.dataset.recordId = recordData.id;
    newRow.className = 'clickable-expense-row';
    newRow.innerHTML = `
      <td></td>
      <td>
        <button class="btn p-0 border-0 bg-transparent icon-btn delete-record-btn"
                data-record-type="salary"
                data-record-id="${recordData.id}">
          <i class="bi bi-trash text-danger fs-5"></i>
        </button>
      </td>
      <td>Выплата зарплаты</td>
      <td>${recordData.comment || ''}</td>
      <td>${recordData.amount}</td>
    `;
    tableBody.appendChild(newRow);

    // Обновляем нумерацию
    updateExpenseRowNumbers();

    // Обновляем общую сумму расходов
    updateExpensesTotal();
  }

  // Функция для обновления итоговой суммы финансовых операций
  function updateExpensesTotal() {
    let total = 0;
    // Собираем все строки финансовых операций
    document.querySelectorAll('#expenses-table-body tr[data-record-id]').forEach(row => {
      // Сумма находится в ячейке с индексом 4 (пятый столбец)
      const amountCell = row.cells[4];
      if (amountCell) {
        const amountText = amountCell.textContent.trim();
        // Парсим число, удаляя все нечисловые символы
        const amount = parseFloat(amountText.replace(/[^\d,.]/g, '').replace(',', '.')) || 0;
        total += amount;
      }
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
      totalExpenseCell.textContent = formattedTotal;
    }

    // Обновляем элемент в финансовой сводке
    const financeExpenseElement = document.getElementById('finance-expense');
    if (financeExpenseElement) {
      financeExpenseElement.textContent = formattedTotal;
    }

    return total;
  }

  // Обновляем обработчик отправки формы расхода
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

            // Обновляем таблицу финансовых операций
            const tableBody = document.getElementById('expenses-table-body');
            const expenseRow = document.querySelector(`tr[data-record-id="${data.expense.id}"][data-record-type="expense"]`);

            if (expenseRow) {
              // Обновляем существующую строку
              expenseRow.innerHTML = `
                    <td>${expenseRow.querySelector('td:first-child').textContent}</td>
                    <td>
                        <button class="btn p-0 border-0 bg-transparent icon-btn delete-record-btn"
                                data-record-type="expense"
                                data-record-id="${data.expense.id}">
                            <i class="bi bi-trash text-danger fs-5"></i>
                        </button>
                    </td>
                    <td>${data.expense.category_display}</td>
                    <td>${data.expense.comment || ''}</td>
                    <td>${data.expense.amount}</td>
                  `;
            } else {
              // Добавляем новую строку
              updateExpensesTable(data.expense);
            }

            showToast('Расход успешно сохранен', 'success');
            updateFinanceSummary();
            updateExpensesTotal();
            updateExpenseRowNumbers();
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

  // Обновляем обработчик выплаты зарплаты
  function paySalary(employeeId, employeeName, salaryAmount, scheduleId) {
    const normalizedAmount = salaryAmount.replace(',', '.');

    const formData = new FormData();
    formData.append('action', 'pay_salary');
    formData.append('employee_id', employeeId);
    formData.append('amount', normalizedAmount);

    fetch(`/schedule/${scheduleId}/`, {
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
          showToast('Зарплата успешно выплачена', 'success');

          // Обновляем отображение зарплаты и скрываем кнопку
          updateSalaryDisplay(employeeId, salaryAmount);

          // Обновляем таблицу финансовых операций
          updateExpensesTableAfterSalary({
            id: data.salary.id,
            type: 'salary',
            category_display: 'Выплата зарплаты',
            comment: `Зарплата сотрудника ${employeeName}`,
            amount: data.salary.total_payment
          });

          // Обновляем финансовую сводку
          updateFinanceSummary();

          // Обновляем итоги расходов
          updateExpensesTotal();
        } else {
          showToast(data.error || 'Ошибка при выплате зарплаты', 'error');
        }
      })
      .catch(error => {
        console.error('Error:', error);
        showToast('Произошла ошибка при выплате зарплаты', 'error');
      });
  }

  // Обновляем обработчик кликов по строкам учеников (игнорировать кнопки платежей)
  document.querySelectorAll('#attendance-body tr[data-student-id]').forEach(row => {
    row.addEventListener('click', function (e) {
      // Игнорируем клики на:
      // - ячейках посещения
      // - кнопке удаления
      // - кнопке платежа
      const ignoredElements = [
        '.attendance-cell',
        '.remove-student-attendance',
        '.student-payment-btn',
        '.bi-cash' // Иконка внутри кнопки платежа
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
    balanceCell.textContent = formatter.format(balance);

    // Добавляем цвет в зависимости от результата
    balanceCell.classList.remove('text-success', 'text-danger');
    if (balance > 0) {
      balanceCell.classList.add('text-success');
    } else if (balance < 0) {
      balanceCell.classList.add('text-danger');
    }

    return balance;
  }

  // При изменении ставки сотрудника обновляем связанные зарплаты
  function updateEmployeeRate(employeeId, newRate) {
    fetch(`/api/employees/${employeeId}/update_salaries/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': CSRF_TOKEN
      },
      body: JSON.stringify({ rate_per_day: newRate })
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          showToast('Ставка обновлена во всех связанных зарплатах', 'success');
        }
      });
  }

  // Обновленная функция colorizePaymentCells()
  function colorizePaymentCells() {
    const rows = document.querySelectorAll('#attendance-body tr[data-student-id]');

    rows.forEach(row => {
      const costCell = row.cells[2]; // Ячейка стоимости
      const paymentCell = row.cells[3]; // Ячейка платежей
      const balanceCell = row.cells[4]; // Ячейка баланса

      // Получаем числовые значения
      const cost = parseFloat(costCell.textContent) || 0;
      const paymentText = paymentCell.textContent.trim();
      const payment = paymentText === '—' ? 0 : parseFloat(paymentText) || 0;
      const balance = payment - cost;

      // УДАЛЯЕМ старые классы подсветки из ячеек платежей (если они есть)
      paymentCell.classList.remove('payment-success', 'payment-danger');

      // Обновляем текст баланса
      balanceCell.textContent = balance.toFixed(2);

      // Убираем все старые классы из ячейки баланса
      balanceCell.classList.remove('text-success', 'text-danger', 'text-muted', 'balance-positive', 'balance-negative', 'balance-zero');

      // ДОБАВЛЯЕМ ПРАВИЛЬНЫЕ КЛАССЫ ПОДСВЕТКИ В ЯЧЕЙКУ БАЛАНСА
      if (balance > 0) {
        balanceCell.classList.add('balance-positive');
      } else if (balance < 0) {
        balanceCell.classList.add('balance-negative');
      } else {
        balanceCell.classList.add('balance-zero');
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

  // Функция для обработки выбора ученика из datalist
  function setupStudentSearch() {
    const searchInput = document.getElementById('student-search-input');
    const idInput = document.getElementById('student-id-input');
    const datalist = document.getElementById('students-datalist');

    if (!searchInput || !idInput) return;

    // Обработчик изменения значения в поле поиска
    searchInput.addEventListener('input', function () {
      const value = this.value.trim();
      const option = Array.from(datalist.options).find(opt => opt.value === value);

      if (option) {
        idInput.value = option.getAttribute('data-id');
      } else {
        idInput.value = '';
      }
    });

    // Обработчик отправки формы - проверяем, что ученик выбран
    const form = document.getElementById('student-form-attendance');
    if (form) {
      form.addEventListener('submit', function (e) {
        if (!idInput.value) {
          e.preventDefault();
          showToast('Пожалуйста, выберите ученика из списка', 'error');
          searchInput.focus();
        }
      });
    }
  }

  // Обновляем доступный баланс при изменении суммы
  document.addEventListener('input', function (e) {
    if (e.target.name === 'amount') {
      updatePaymentFormBalance();
    }
  });

  // Обработчик для кнопки выплаты зарплаты
  document.addEventListener('click', function (e) {
    const payBtn = e.target.closest('.pay-salary-btn');
    if (payBtn) {
      e.preventDefault();
      e.stopPropagation();

      const employeeId = payBtn.dataset.employeeId;
      const employeeName = payBtn.dataset.employeeName;
      let salaryAmount = payBtn.dataset.salaryAmount;
      const scheduleId = payBtn.dataset.scheduleId;

      // Нормализуем сумму (заменяем запятую на точку если нужно)
      salaryAmount = salaryAmount.replace(',', '.');

      if (confirm(`Выплатить зарплату сотруднику ${employeeName} в размере ${salaryAmount} руб.?`)) {
        paySalary(employeeId, employeeName, salaryAmount, scheduleId);
      }
    }
  });

  // Функция для нормализации числовых значений (запятая -> точка)
  function normalizeDecimal(value) {
    if (typeof value === 'string') {
      return value.replace(',', '.');
    }
    return value;
  }

  // Функция для обновления отображения зарплаты после выплаты
  function updateSalaryDisplay(employeeId, amount) {
    const salaryCell = document.querySelector(`#employee-${employeeId} .salary-amount`);
    if (salaryCell) {
      // Форматируем сумму с запятой для отображения
      const formattedAmount = parseFloat(amount).toFixed(2).replace('.', ',');
      salaryCell.innerHTML = `<span class="text-success">выплачено ${formattedAmount}</span>`;
    }

    // Скрываем кнопку выплаты
    const payBtn = document.querySelector(`.pay-salary-btn[data-employee-id="${employeeId}"]`);
    if (payBtn) {
      payBtn.style.display = 'none';
    }
  }

  // Функция для инициализации состояния кнопок выплаты при загрузке страницы
  function initializePaymentButtons() {
    document.querySelectorAll('.pay-salary-btn').forEach(btn => {
      const employeeId = btn.dataset.employeeId;
      const salaryCell = document.querySelector(`#employee-${employeeId} .salary-amount`);

      // Если в ячейке зарплаты уже есть текст "выплачено", скрываем кнопку
      if (salaryCell && salaryCell.querySelector('.text-success')) {
        btn.classList.add('d-none');
        btn.style.display = 'none';
      } else {
        // Убеждаемся, что кнопка видима и имеет правильные классы
        btn.classList.remove('d-none');
        btn.style.display = 'inline-block';
        btn.classList.add('btn', 'p-0', 'border-0', 'bg-transparent', 'icon-btn', 'pay-salary-btn');
      }
    });
  }
  
  const employeeCardHeader = document.querySelector('.card .card-header.bg-primary.text-white');
  if (employeeCardHeader && employeeCardHeader.textContent.includes('Сотрудники группы')) {
    const employeeCard = employeeCardHeader.closest('.card');
    const employeeCardBody = employeeCard.querySelector('.card-body');

    // Добавляем класс для анимации
    employeeCardBody.classList.add('collapsible-content');

    // Добавляем курсор pointer и стрелку для индикации кликабельности
    employeeCardHeader.style.cursor = 'pointer';
    employeeCardHeader.innerHTML = '<h3 class="d-flex justify-content-between align-items-center m-0">Сотрудники группы <span class="collapse-arrow">▼</span></h3>';

    employeeCardHeader.addEventListener('click', function () {
      if (employeeCardBody.classList.contains('collapsed')) {
        // Разворачиваем
        employeeCardBody.style.maxHeight = employeeCardBody.scrollHeight + 'px';
        employeeCardBody.classList.remove('collapsed');
        employeeCardHeader.querySelector('.collapse-arrow').textContent = '▼';

        // Удаляем max-height после анимации для корректного отображения при изменении размера
        setTimeout(() => {
          if (!employeeCardBody.classList.contains('collapsed')) {
            employeeCardBody.style.maxHeight = 'none';
          }
        }, 300);
      } else {
        // Сворачиваем
        employeeCardBody.style.maxHeight = employeeCardBody.scrollHeight + 'px';
        // Даем браузеру время применить max-height
        requestAnimationFrame(() => {
          employeeCardBody.style.maxHeight = '0';
          employeeCardBody.classList.add('collapsed');
          employeeCardHeader.querySelector('.collapse-arrow').textContent = '▶';
        });
      }
    });
  }

  

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
    initializePaymentButtons();
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