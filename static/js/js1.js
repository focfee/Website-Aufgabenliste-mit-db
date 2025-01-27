class TaskManager {
    constructor() {
        this.init();
    }
    init() {
        document.getElementById('add-card').addEventListener('click', () => this.addTask());
        document.getElementById('filter_tasks').addEventListener('change', (event) => this.filterTasks(event.target.value));
        document.getElementById('filter_search').addEventListener('input', (event) => this.filterSearch(event.target.value));
        this.loadTasks('/tasks');
    }
    addTask() {
        const today = new Date().toISOString().split('T')[0];
        const newTask = {
            name: 'Новое дело',
            status: 'создано',
            data: today
        };
        fetch('/tasks/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(newTask)
        }).then(response => response.json())
          .then(task => {
              this.createCard(task);
          })
    }
    createCard(task) {
        const container = document.getElementById('cards-container');
        const newCard = document.createElement('div');
        newCard.className = 'card';
        newCard.dataset.id = task.id;
        newCard.innerHTML = `
        <div class="pin_decor"><p>📌</p><p>📌</p></div>
            <div class="card_header">
                <h3 class="name"><span class="name-text">${task.name}</span><input type="text" class="edit_name" value="${task.name}" maxlength="45"></h3>             
                <button class="change_button" title="Редактировать дело">✏️</button>
                <button class="delete_button" style="display: none;">🗑️</button>
            </div>  
            <li class="status">Статус: <span class="status-text">${task.status}</span>
                <select class="edit_status">
                    <option value="создано" ${task.status === 'создано' ? 'selected' : ''}>создано</option>
                    <option value="начата работа" ${task.status === 'начата работа' ? 'selected' : ''}>начата работа</option>
                    <option value="закончена работа" ${task.status === 'закончена работа' ? 'selected' : ''}>закончена работа</option>
                </select>
            </li>
            <li class="data">Дата окончания: <span class="data-text">${task.data}</span><input type="date" class="edit_date" value="${task.data}"></li>
        `;
        container.appendChild(newCard);
        this.addCardEventListeners(newCard);
    }
    addCardEventListeners(card) {
        const changeButton = card.querySelector('.change_button');
        const deleteButton = card.querySelector('.delete_button');
        const nameText = card.querySelector('.name-text');
        const nameInput = card.querySelector('.edit_name');
        const statusText = card.querySelector('.status-text');
        const statusSelect = card.querySelector('.edit_status');
        const dataText = card.querySelector('.data-text');
        const dataInput = card.querySelector('.edit_date');
        changeButton.addEventListener('click', () => {
            if (changeButton.innerText === '✏️') {
                nameText.style.display = 'none';
                nameInput.style.display = 'inline';
                nameInput.title = 'Редактировать название дела';
                statusText.style.display = 'none';
                statusSelect.style.display = 'inline';
                statusSelect.title = 'Редактировать статус дела';
                dataText.style.display = 'none';
                dataInput.style.display = 'inline';
                dataInput.title = 'Редактировать дату дела';
                deleteButton.style.display = 'inline';
                deleteButton.title = 'Удалить дело';
                changeButton.innerText = '✔️';
                changeButton.title = 'Сохранить редактирование дела';
            } else {
                const name = nameInput.value;
                if (name.length > 45) {
                    alert ('Название дела не должно превышать 45 символов');
                    return;
                }
                const status = statusSelect.value;
                const date = dataInput.value;

                fetch(`/tasks/update/${card.dataset.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ name, status, data: date })
                }).then(response => response.json())
                  .then(updatedTask => {
                      nameText.innerText = updatedTask.name;
                      statusText.innerText = updatedTask.status;
                      dataText.innerText = updatedTask.data;

                      nameText.style.display = 'inline';
                      nameInput.style.display = 'none';
                      statusText.style.display = 'inline';
                      statusSelect.style.display = 'none';
                      dataText.style.display = 'inline';
                      dataInput.style.display = 'none';
                      deleteButton.style.display = 'none';
                      changeButton.title = 'Редактировать дело';
                      changeButton.innerText = '✏️';
                  })
            }
        });
        deleteButton.addEventListener('click', () => {
            fetch(`/tasks/delete/${card.dataset.id}`, {
                method: 'DELETE'
            }).then(response => {
                if (response.ok) {
                    card.remove();
                }
            });
        });
    }
    loadTasks(url) {
        fetch(url)
            .then(response => response.json())
            .then(tasks => {
                const container = document.getElementById('cards-container');
                container.innerHTML = '';
                tasks.forEach(task => this.createCard(task));
            })
    }
    filterTasks(filter) {
        let url = '/tasks';
        if (filter === 'overdue') {
            url = '/tasks/overdue';
        } else if (filter !== 'all') {
            url = `/tasks/status/${filter}`;
        }
        this.loadTasks(url);
    }
    filterSearch(query) {
        const cards = document.querySelectorAll('.card');
        query = query.toLowerCase();
        cards.forEach(card => {
            const title = card.querySelector('.name-text').innerText.toLowerCase();
            if (title.includes(query)) {
            card.style.display = 'block';
            } else {
            card.style.display= 'none';
            }
        });
    }
}
new TaskManager();