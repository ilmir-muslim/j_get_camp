document.addEventListener('DOMContentLoaded', function () {
    // Элементы страницы
    const addBranchBtn = document.getElementById('add-branch-btn');
    const saveBranchBtn = document.getElementById('save-branch-btn');
    const updateBranchBtn = document.getElementById('update-branch-btn');
    const confirmDeleteBranchBtn = document.getElementById('confirm-delete-branch-btn');
    const branchSearch = document.getElementById('branch-search');
    const branchesTable = document.getElementById('branches-table');

    // Модальные окна
    const createBranchModal = new bootstrap.Modal(document.getElementById('createBranchModal'));
    const editBranchModal = new bootstrap.Modal(document.getElementById('editBranchModal'));
    const deleteBranchModal = new bootstrap.Modal(document.getElementById('deleteBranchModal'));
    const viewBranchModal = new bootstrap.Modal(document.getElementById('viewBranchModal'));

    // Переменные для хранения состояния
    let currentBranchId = null;

    // Поиск филиалов
    branchSearch.addEventListener('input', function () {
        const searchText = this.value.toLowerCase();
        const rows = branchesTable.getElementsByTagName('tbody')[0].getElementsByTagName('tr');

        for (let row of rows) {
            const name = row.cells[2].textContent.toLowerCase();
            const address = row.cells[3].textContent.toLowerCase();

            if (name.includes(searchText) || address.includes(searchText)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        }
    });

    // Открытие модального окна для создания филиала
    addBranchBtn.addEventListener('click', function () {
        document.getElementById('create-branch-form').reset();
        createBranchModal.show();
    });

    // Создание филиала
    saveBranchBtn.addEventListener('click', function () {
        const formData = new FormData(document.getElementById('create-branch-form'));
        const data = {
            name: formData.get('name'),
            address: formData.get('address')
        };

        fetch(API_BRANCHES_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify(data)
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(errorData => {
                        throw new Error(errorData.error || 'Ошибка при создании филиала');
                    });
                }
                return response.json();
            })
            .then(data => {
                addBranchToTable(data);
                createBranchModal.hide();
                showToast('Филиал успешно создан', 'success');
            })
            .catch(error => {
                console.error('Error:', error);
                showToast(error.message, 'error');
            });
    });

    // Обработчики событий
    document.addEventListener('click', function (e) {
        if (e.target.closest('.edit-branch-btn')) {
            const branchId = e.target.closest('.edit-branch-btn').dataset.branchId;
            currentBranchId = branchId;

            fetch(`${API_BRANCHES_URL}${branchId}/`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Филиал не найден');
                    }
                    return response.json();
                })
                .then(branch => {
                    document.getElementById('edit-branch-id').value = branch.id;
                    document.getElementById('edit-branch-name').value = branch.name;
                    document.getElementById('edit-branch-address').value = branch.address;
                    editBranchModal.show();
                })
                .catch(error => {
                    console.error('Error:', error);
                    showToast(error.message, 'error');
                });
        }

        if (e.target.closest('.delete-branch-btn')) {
            const branchId = e.target.closest('.delete-branch-btn').dataset.branchId;
            const branchName = e.target.closest('tr').cells[2].textContent;
            currentBranchId = branchId;

            document.getElementById('delete-branch-name').textContent = branchName;
            deleteBranchModal.show();
        }

        if (e.target.closest('.view-branch-btn')) {
            const branchId = e.target.closest('.view-branch-btn').dataset.branchId;
            currentBranchId = branchId;
            loadBranchDetails(branchId);
        }
    });

    // Обновление филиала
    updateBranchBtn.addEventListener('click', function () {
        const formData = new FormData(document.getElementById('edit-branch-form'));
        const data = {
            name: formData.get('name'),
            address: formData.get('address')
        };

        fetch(`${API_BRANCHES_URL}${currentBranchId}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
            body: JSON.stringify(data)
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(errorData => {
                        throw new Error(errorData.error || 'Ошибка при обновлении филиала');
                    });
                }
                return response.json();
            })
            .then(updatedBranch => {
                updateBranchInTable(updatedBranch);
                editBranchModal.hide();
                showToast('Филиал успешно обновлен', 'success');
            })
            .catch(error => {
                console.error('Error:', error);
                showToast(error.message, 'error');
            });
    });

    // Удаление филиала
    confirmDeleteBranchBtn.addEventListener('click', function () {
        fetch(`${API_BRANCHES_URL}${currentBranchId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': CSRF_TOKEN
            }
        })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(errorData => {
                        throw new Error(errorData.error || 'Ошибка при удалении филиала');
                    });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    document.getElementById(`branch-${currentBranchId}`).remove();
                    deleteBranchModal.hide();
                    showToast('Филиал успешно удален', 'success');
                } else {
                    throw new Error(data.error || 'Ошибка при удалении филиала');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast(error.message, 'error');
            });
    });

    // Функция загрузки деталей филиала
    function loadBranchDetails(branchId) {
        fetch(`${API_BRANCHES_URL}${branchId}/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Филиал не найден');
                }
                return response.json();
            })
            .then(branch => {
                document.getElementById('branch-detail-name').textContent = branch.name;
                document.getElementById('branch-detail-address').textContent = branch.address || 'Не указан';

                return fetch(`${API_EMPLOYEES_URL}?branch_id=${branchId}`);
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Ошибка загрузки сотрудников');
                }
                return response.json();
            })
            .then(employees => {
                const tableBody = document.querySelector('#branch-employees-table tbody');
                const noEmployeesMsg = document.getElementById('no-employees-message');

                tableBody.innerHTML = '';

                if (employees.length > 0) {
                    noEmployeesMsg.classList.add('d-none');

                    employees.forEach(employee => {
                        const row = tableBody.insertRow();
                        row.innerHTML = `
                            <td>${escapeHtml(employee.full_name)}</td>
                            <td>${escapeHtml(getPositionDisplay(employee.position))}</td>
                            <td>${employee.schedule_id ? 'Смена #' + employee.schedule_id : 'Не назначена'}</td>
                            <td>${employee.rate_per_day ? formatCurrency(employee.rate_per_day) : 'Не указана'}</td>
                        `;
                    });
                } else {
                    noEmployeesMsg.classList.remove('d-none');
                }

                viewBranchModal.show();
            })
            .catch(error => {
                console.error('Error:', error);
                showToast(error.message, 'error');
            });
    }

    // Вспомогательные функции
    function addBranchToTable(branch) {
        const tbody = branchesTable.getElementsByTagName('tbody')[0];
        const rowCount = tbody.rows.length;

        const row = tbody.insertRow();
        row.id = `branch-${branch.id}`;

        row.innerHTML = `
            <td>${rowCount + 1}</td>
            <td>
                <button class="btn p-0 border-0 bg-transparent icon-btn edit-branch-btn"
                        data-branch-id="${branch.id}">
                    <i class="bi bi-pencil text-primary"></i>
                </button>
                <button class="btn p-0 border-0 bg-transparent icon-btn delete-branch-btn"
                        data-branch-id="${branch.id}">
                    <i class="bi bi-trash text-danger"></i>
                </button>
                <button class="btn p-0 border-0 bg-transparent icon-btn view-branch-btn"
                        data-branch-id="${branch.id}"
                        data-bs-toggle="tooltip" title="Просмотр деталей">
                    <i class="bi bi-eye text-info"></i>
                </button>
            </td>
            <td>${branch.name}</td>
            <td>${branch.address}</td>
        `;
    }

    function updateBranchInTable(branch) {
        const row = document.getElementById(`branch-${branch.id}`);
        if (row) {
            row.cells[2].textContent = branch.name;
            row.cells[3].textContent = branch.address;
        }
    }

    function getPositionDisplay(position) {
        const positions = {
            'teacher': 'Преподаватель',
            'admin': 'Администратор',
            'camp_head': 'Начальник лагеря',
            'lab_head': 'Начальник лаборатории'
        };
        return positions[position] || position;
    }

    function formatCurrency(amount) {
        return new Intl.NumberFormat('ru-RU', {
            style: 'currency',
            currency: 'RUB',
            minimumFractionDigits: 0
        }).format(amount);
    }

    function escapeHtml(str) {
        return str.replace(/[&<>"']/g, function (match) {
            const escapes = {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            };
            return escapes[match];
        });
    }
});