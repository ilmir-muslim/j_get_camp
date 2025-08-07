// JavaScript для формы лидов
document.addEventListener('DOMContentLoaded', function() {
  const dateField = document.querySelector('input[type="date"]');
  const timeField = document.querySelector('input[type="time"]');
  const datetimeField = document.querySelector('input[type="datetime-local"]');
  
  // Обработка поля datetime-local
  if (datetimeField) {
    datetimeField.addEventListener('change', function() {
      if (this.value && !this.value.includes('T')) {
        const now = new Date();
        const timeString = now.toTimeString().substring(0, 5);
        this.value = this.value + 'T' + timeString;
      }
    });
  }
  // Обработка раздельных полей даты и времени
  else if (dateField && timeField) {
    dateField.addEventListener('change', function() {
      if (this.value && !timeField.value) {
        const now = new Date();
        timeField.value = now.toTimeString().substring(0, 5);
      }
    });
  }
});