// JavaScript для списка смен
document.addEventListener('DOMContentLoaded', function() {
  // Обработка кликов по кликабельным ячейкам
  document.querySelectorAll('.clickable-cell').forEach(function(cell) {
    cell.addEventListener('click', function() {
      const url = this.getAttribute('data-url');
      if (url) {
        window.location.href = url;
      }
    });
  });
});