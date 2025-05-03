document.addEventListener('DOMContentLoaded', () => {
    const userTableBody = document.querySelector('#userTable tbody');

    // Função para carregar usuários
    async function loadUsers() {
        try {
            const response = await fetch('/admin/users', {
                headers: {
                    'x-access-token': localStorage.getItem('token')
                }
            });

            if (!response.ok) {
                throw new Error('Erro ao carregar usuários');
            }

            const users = await response.json();
            userTableBody.innerHTML = '';

            users.forEach(user => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${user[0]}</td>
                    <td>${user[1]}</td>
                    <td>
                        <button class="delete-btn" data-id="${user[0]}">Excluir</button>
                    </td>
                `;
                userTableBody.appendChild(row);
            });
        } catch (error) {
            console.error(error);
        }
    }

    // Função para excluir usuário
    async function deleteUser(userId) {
        try {
            const response = await fetch(`/admin/users/${userId}`, {
                method: 'DELETE',
                headers: {
                    'x-access-token': localStorage.getItem('token')
                }
            });

            if (!response.ok) {
                throw new Error('Erro ao excluir usuário');
            }

            alert('Usuário excluído com sucesso');
            loadUsers();
        } catch (error) {
            console.error(error);
        }
    }

    // Evento para excluir usuário ao clicar no botão
    userTableBody.addEventListener('click', (event) => {
        if (event.target.classList.contains('delete-btn')) {
            const userId = event.target.getAttribute('data-id');
            deleteUser(userId);
        }
    });

    // Carrega os usuários ao iniciar
    loadUsers();
});