// Обработка кликов по строкам таблицы
document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.clickable-row').forEach(function (row) {
    row.addEventListener('click', function () {
      const url = this.dataset.url;
      if (url) {
        window.location.href = url;
      }
    });
  });
});