// Configuración del logger
const Logger = {
    info: (message, data = null) => {
        console.log(`[INFO] ${message}`, data || '');
    },
    error: (message, error = null) => {
        console.error(`[ERROR] ${message}`, error || '');
    },
    warn: (message, data = null) => {
        console.warn(`[WARN] ${message}`, data || '');
    },
    debug: (message, data = null) => {
        console.debug(`[DEBUG] ${message}`, data || '');
    }
};

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar elementos
    function initializeElements() {
        // Solo obtener los elementos que existen en el HTML
        const elements = {
            searchInput: document.getElementById('searchInput'),
            statusFilter: document.getElementById('statusFilter'),
            typeFilter: document.getElementById('typeFilter'),
            clientDetailsModal: document.getElementById('clientDetailsModal'),
            deleteConfirmModal: document.getElementById('deleteConfirmModal'),
            notificationContainer: document.getElementById('notification-container')
        };

        // Agregar event listeners solo si los elementos existen
        if (elements.searchInput) {
            elements.searchInput.addEventListener('input', () => filterClients(elements));
        }

        if (elements.statusFilter) {
            elements.statusFilter.addEventListener('change', () => filterClients(elements));
        }

        if (elements.typeFilter) {
            elements.typeFilter.addEventListener('change', () => filterClients(elements));
        }

        return elements;
    }

    // Función de filtrado
    function filterClients(elements) {
        const searchTerm = elements.searchInput?.value?.toLowerCase() || '';
        const statusValue = elements.statusFilter?.value?.toLowerCase() || '';
        const typeValue = elements.typeFilter?.value?.toLowerCase() || '';

        const rows = document.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const statusCell = row.querySelector('td:nth-child(5)');
            const typeCell = row.querySelector('td:nth-child(3)');
            
            const status = statusCell?.textContent?.toLowerCase().trim() || '';
            const type = typeCell?.textContent?.toLowerCase().trim() || '';

            const matchesSearch = text.includes(searchTerm);
            const matchesStatus = statusValue === '' || status.includes(statusValue);
            const matchesType = typeValue === '' || type.includes(typeValue);

            row.style.display = matchesSearch && matchesStatus && matchesType ? '' : 'none';
        });
    }

    // Función para mostrar notificaciones
    function showNotification(message, type = 'success') {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const notification = document.createElement('div');
        notification.className = `${type === 'success' ? 'bg-green-500' : 'bg-red-500'} text-white px-6 py-3 rounded-lg shadow-lg`;
        notification.textContent = message;
        container.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    // Funciones para manejo de modales
    window.showClientDetails = async function(clientId) {
        const modal = document.getElementById('clientDetailsModal');
        if (!modal) return;

        try {
            const response = await fetch(`/clients/${clientId}/details`);
            const client = await response.json();

            // Actualizar campos del modal
            const fields = {
                clientName: client.name,
                businessName: client.business_name,
                taxId: client.tax_id,
                clientType: client.client_type
            };

            Object.entries(fields).forEach(([id, value]) => {
                const element = document.getElementById(id);
                if (element) element.textContent = value || '';
            });

            // Actualizar botón de edición
            const editButton = document.getElementById('editClientButton');
            if (editButton) {
                editButton.href = `/clients/${clientId}/edit`;
            }

            modal.classList.remove('hidden');
            initializeTabs();
        } catch (error) {
            console.error('Error al cargar detalles:', error);
            showNotification('Error al cargar los detalles del cliente', 'error');
        }
    };

    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.classList.add('hidden');
    };

    window.confirmDelete = function(clientId) {
        const modal = document.getElementById('deleteConfirmModal');
        if (modal) {
            window.clientToDelete = clientId;
            modal.classList.remove('hidden');
        }
    };

    window.executeDelete = async function() {
        const clientId = window.clientToDelete;
        if (!clientId) return;

        try {
            const response = await fetch(`/clients/${clientId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
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
                closeModal('deleteConfirmModal');
            } else {
                throw new Error(data.error || 'Error al eliminar el cliente');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification(error.message || 'Error al eliminar el cliente', 'error');
        }
    };

    function initializeTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.getAttribute('data-tab');
                
                tabButtons.forEach(btn => {
                    btn.classList.remove('text-blue-600', 'border-blue-600');
                    btn.classList.add('text-gray-500', 'border-transparent');
                });
                button.classList.add('text-blue-600', 'border-blue-600');
                button.classList.remove('text-gray-500', 'border-transparent');

                tabContents.forEach(content => {
                    content.classList.toggle('hidden', content.id !== `${tabName}Tab`);
                });
            });
        });
    }

    // Inicializar la aplicación
    const elements = initializeElements();

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