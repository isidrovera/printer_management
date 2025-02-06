document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos DOM
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    const typeFilter = document.getElementById('typeFilter');
    const notificationContainer = document.getElementById('notification-container');

    // Función para mostrar notificaciones
    function showNotification(message, type = 'success') {
        const notification = document.createElement('div');
        notification.className = `${type === 'success' ? 'bg-green-500' : 'bg-red-500'} text-white px-6 py-3 rounded-lg shadow-lg transition-opacity duration-300`;
        notification.textContent = message;
        notificationContainer.appendChild(notification);

        // Eliminar después de 3 segundos
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    // Función de búsqueda y filtrado
    function filterClients() {
        const searchTerm = searchInput.value.toLowerCase();
        const statusValue = statusFilter.value.toLowerCase();
        const typeValue = typeFilter.value.toLowerCase();
        const rows = document.querySelectorAll('tbody tr');

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const status = row.querySelector('td:nth-child(5)').textContent.toLowerCase();
            const type = row.querySelector('td:nth-child(3)').textContent.toLowerCase();

            const matchesSearch = text.includes(searchTerm);
            const matchesStatus = statusValue === '' || status.includes(statusValue);
            const matchesType = typeValue === '' || type.includes(typeValue);

            row.style.display = matchesSearch && matchesStatus && matchesType ? '' : 'none';
        });
    }

    // Event listeners para búsqueda y filtros
    if (searchInput) {
        searchInput.addEventListener('input', filterClients);
    }
    if (statusFilter) {
        statusFilter.addEventListener('change', filterClients);
    }
    if (typeFilter) {
        typeFilter.addEventListener('change', filterClients);
    }

    // Manejo de tabs en el modal de detalles
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            
            // Actualizar clases de botones
            tabButtons.forEach(btn => {
                btn.classList.remove('text-blue-600', 'border-blue-600');
                btn.classList.add('text-gray-500', 'border-transparent');
            });
            button.classList.add('text-blue-600', 'border-blue-600');
            button.classList.remove('text-gray-500', 'border-transparent');

            // Mostrar contenido de tab seleccionado
            tabContents.forEach(content => {
                if (content.id === `${tabName}Tab`) {
                    content.classList.remove('hidden');
                } else {
                    content.classList.add('hidden');
                }
            });
        });
    });

    // Funciones para modales
    window.showClientDetails = function(clientId) {
        const modal = document.getElementById('clientDetailsModal');
        if (modal) {
            modal.classList.remove('hidden');
            // Aquí irían las llamadas a la API para cargar los detalles del cliente
            loadClientDetails(clientId);
        }
    };

    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
        }
    };

    window.confirmDelete = async function(clientId) {
        const modal = document.getElementById('deleteConfirmModal');
        if (modal) {
            modal.classList.remove('hidden');
            window.clientToDelete = clientId; // Guardar el ID para usar en executeDelete
        }
    };

    window.executeDelete = async function() {
        const clientId = window.clientToDelete;
        if (!clientId) return;

        try {
            const response = await fetch(`/clients/${clientId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken() // Función para obtener el token CSRF
                }
            });

            const data = await response.json();

            if (data.success) {
                showNotification('Cliente eliminado con éxito');
                const row = document.querySelector(`tr[data-client-id="${clientId}"]`);
                if (row) {
                    row.style.animation = 'fadeOut 0.3s ease';
                    setTimeout(() => row.remove(), 300);
                }
            } else {
                showNotification(data.error || 'Error al eliminar el cliente', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Error al eliminar el cliente', 'error');
        }

        closeModal('deleteConfirmModal');
    };

    // Función para obtener el token CSRF
    function getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Función para cargar detalles del cliente
    async function loadClientDetails(clientId) {
        try {
            const response = await fetch(`/clients/${clientId}/details`);
            const client = await response.json();

            // Actualizar información básica
            document.getElementById('clientName').textContent = client.name;
            document.getElementById('businessName').textContent = client.business_name;
            document.getElementById('taxId').textContent = client.tax_id;
            document.getElementById('clientType').textContent = client.client_type;

            // Actualizar estado y métricas
            const statusElement = document.getElementById('clientStatus');
            statusElement.textContent = client.status;
            statusElement.className = `px-3 py-1 rounded-full text-sm font-medium ${
                client.status === 'activo' ? 'bg-green-100 text-green-800' :
                client.status === 'inactivo' ? 'bg-red-100 text-red-800' :
                'bg-gray-100 text-gray-800'
            }`;

            // Actualizar enlace de edición
            const editButton = document.getElementById('editClientButton');
            if (editButton) {
                editButton.href = `/clients/${clientId}/edit`;
            }

        } catch (error) {
            console.error('Error cargando detalles:', error);
            showNotification('Error al cargar los detalles del cliente', 'error');
        }
    }

    // Agregar estilos de animación
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeOut {
            from { opacity: 1; transform: translateY(0); }
            to { opacity: 0; transform: translateY(-10px); }
        }
    `;
    document.head.appendChild(style);
});