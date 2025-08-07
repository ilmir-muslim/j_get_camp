// Базовая функциональность для всех страниц
document.addEventListener('DOMContentLoaded', function() {
  // Инициализация всплывающих подсказок
  const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  const tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
  
  // Инициализация всплывающих окон
  const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
  const popoverList = popoverTriggerList.map(function(popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl);
  });
  
  // Функция для показа уведомлений
  window.showToast = function(message, type) {
    const toastEl = document.getElementById('liveToast');
    const toastBody = toastEl.querySelector('.toast-body');
    const toast = new bootstrap.Toast(toastEl);
    
    toastEl.classList.remove('bg-success', 'bg-danger', 'bg-warning');
    toastBody.textContent = message;
    
    if (type === 'success') toastEl.classList.add('bg-success', 'text-white');
    else if (type === 'error') toastEl.classList.add('bg-danger', 'text-white');
    else if (type === 'warning') toastEl.classList.add('bg-warning', 'text-dark');
    
    toast.show();
  };
});
