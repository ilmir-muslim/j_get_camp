// JavaScript для посещаемости сотрудников
document.addEventListener('DOMContentLoaded', function() {
  // Обработка кликов по ячейкам посещаемости
  document.querySelectorAll('.attendance-cell').forEach(cell => {
    cell.addEventListener('click', function() {
      const employeeId = this.dataset.employeeId;
      const dateStr = this.dataset.date;
      
      fetch(TOGGLE_ATTENDANCE_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': CSRF_TOKEN
        },
        body: JSON.stringify({
          employee_id: employeeId,
          date: dateStr
        })
      })
      .then(response => response.json())
      .then(data => {
        if (data.status === 'success') {
          // Обновление визуального состояния
          if (data.present) {
            this.classList.remove('bg-danger');
            this.classList.add('bg-success');
            this.innerHTML = '<i class="bi bi-check-lg text-white"></i>';
          } else {
            this.classList.remove('bg-success');
            this.classList.add('bg-danger');
            this.innerHTML = '<i class="bi bi-x-lg text-white"></i>';
          }
        }
      });
    });
  });
});