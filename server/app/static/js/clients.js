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
    // Sistema de logging
    const Logger = {
        info: (message) => console.log(`[INFO] ${message}`),
        error: (message) => console.error(`[ERROR] ${message}`),
        warn: (message) => console.warn(`[WARN] ${message}`)
    };

    // Función principal de filtrado
    function filterClients() {
        const searchInput = document.getElementById('searchInput');
        const statusFilter = document.getElementById('statusFilter');
        const typeFilter = document.getElementById('typeFilter');
        
        const searchTerm = searchInput?.value?.toLowerCase() || '';
        const statusValue = statusFilter?.value?.toLowerCase() || '';
        const typeValue = typeFilter?.value?.toLowerCase() || '';

        const rows = document.querySelectorAll('tbody tr');
        rows.forEach(row => {
            try {
                const text = row.textContent.toLowerCase();
                const statusCell = row.querySelector('td:nth-child(5)');
                const typeCell = row.querySelector('td:nth-child(3)');
                
                const status = statusCell?.textContent?.toLowerCase().trim() || '';
                const type = typeCell?.textContent?.toLowerCase().trim() || '';

                const matchesSearch = text.includes(searchTerm);
                const matchesStatus = statusValue === '' || status.includes(statusValue);
                const matchesType = typeValue === '' || type.includes(typeValue);

                row.style.display = matchesSearch && matchesStatus && matchesType ? '' : 'none';
            } catch (error) {
                Logger.error('Error al filtrar fila: ' + error);
                row.style.display = '';
            }
        });
    }

    // Inicialización segura de event listeners
    function initializeFilters() {
        const searchInput = document.getElementById('searchInput');
        const statusFilter = document.getElementById('statusFilter');
        const typeFilter = document.getElementById('typeFilter');

        if (searchInput) {
            searchInput.addEventListener('input', filterClients);
        }
        if (statusFilter) {
            statusFilter.addEventListener('change', filterClients);
        }
        if (typeFilter) {
            typeFilter.addEventListener('change', filterClients);
        }
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

    // Funciones globales
    window.showClientDetails = async function(clientId) {
        const modal = document.getElementById('clientDetailsModal');
        if (!modal) return;

        try {
            const response = await fetch(`/clients/${clientId}/details`);
            const client = await response.json();

            // Actualizar información básica
            const elements = {
                clientName: client.name,
                businessName: client.business_name,
                taxId: client.tax_id,
                clientType: client.client_type
            };

            Object.entries(elements).forEach(([id, value]) => {
                const element = document.getElementById(id);
                if (element) element.textContent = value || '';
            });

            modal.classList.remove('hidden');
        } catch (error) {
            Logger.error('Error al cargar detalles del cliente: ' + error);
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
                headers: { 'Content-Type': 'application/json' }
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
            Logger.error('Error al eliminar cliente: ' + error);
            showNotification(error.message, 'error');
        }
    };

    // Inicializar la aplicación
    initializeFilters();

    // Agregar estilos de animación
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeOut {
            from { opacity: 1; transform: translateY(0); }
            to { opacity: 0; transform: translateY(-10px); }
        }
    `;
    document.head.appendChild(style);

    Logger.info('Aplicación inicializada correctamente');
});