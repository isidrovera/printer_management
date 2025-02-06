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
    Logger.info('Iniciando aplicación de gestión de clientes');

    // Objeto para mantener las referencias a elementos DOM
    const elements = {
        searchInput: document.getElementById('searchInput'),
        statusFilter: document.getElementById('statusFilter'),
        typeFilter: document.getElementById('typeFilter'),
        notificationContainer: document.getElementById('notification-container'),
        clientDetailsModal: document.getElementById('clientDetailsModal'),
        deleteConfirmModal: document.getElementById('deleteConfirmModal')
    };

    // Inicialización segura de event listeners
    function initializeEventListeners() {
        Logger.debug('Inicializando event listeners');

        // Event listener para búsqueda
        if (elements.searchInput) {
            elements.searchInput.addEventListener('input', handleFilter);
            Logger.debug('Event listener agregado a searchInput');
        }

        // Event listener para filtro de estado
        if (elements.statusFilter) {
            elements.statusFilter.addEventListener('change', handleFilter);
            Logger.debug('Event listener agregado a statusFilter');
        }

        // Event listener para filtro de tipo
        if (elements.typeFilter) {
            elements.typeFilter.addEventListener('change', handleFilter);
            Logger.debug('Event listener agregado a typeFilter');
        }
    }

    // Función para manejar el filtrado
    function handleFilter() {
        Logger.debug('Ejecutando filtrado');
        
        const searchTerm = elements.searchInput?.value?.toLowerCase() || '';
        const statusValue = elements.statusFilter?.value?.toLowerCase() || '';
        const typeValue = elements.typeFilter?.value?.toLowerCase() || '';

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
                Logger.error('Error al filtrar fila:', error);
                row.style.display = '';
            }
        });
    }

    // Función para mostrar notificaciones
    function showNotification(message, type = 'success') {
        if (!elements.notificationContainer) {
            Logger.error('Contenedor de notificaciones no encontrado');
            return;
        }

        const notification = document.createElement('div');
        notification.className = `${type === 'success' ? 'bg-green-500' : 'bg-red-500'} text-white px-6 py-3 rounded-lg shadow-lg`;
        notification.textContent = message;

        elements.notificationContainer.appendChild(notification);
        setTimeout(() => notification.remove(), 3000);
    }

    // Función para manejar los tabs
    function initializeTabs() {
        const tabButtons = document.querySelectorAll('.tab-button');
        const tabContents = document.querySelectorAll('.tab-content');

        if (!tabButtons.length || !tabContents.length) {
            Logger.warn('No se encontraron elementos de tabs');
            return;
        }

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.getAttribute('data-tab');
                
                // Actualizar botones
                tabButtons.forEach(btn => {
                    btn.classList.remove('text-blue-600', 'border-blue-600');
                    btn.classList.add('text-gray-500', 'border-transparent');
                });
                button.classList.add('text-blue-600', 'border-blue-600');
                button.classList.remove('text-gray-500', 'border-transparent');

                // Actualizar contenido
                tabContents.forEach(content => {
                    content.classList.toggle('hidden', content.id !== `${tabName}Tab`);
                });
            });
        });
    }

    // Funciones globales para la gestión de clientes
    window.showClientDetails = async function(clientId) {
        try {
            const response = await fetch(`/clients/${clientId}/details`);
            const client = await response.json();

            // Actualizar campos
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

            // Actualizar estado
            const statusElement = document.getElementById('clientStatus');
            if (statusElement) {
                statusElement.textContent = client.status;
                statusElement.className = `px-3 py-1 rounded-full text-sm font-medium ${
                    client.status === 'activo' ? 'bg-green-100 text-green-800' :
                    client.status === 'inactivo' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                }`;
            }

            // Mostrar modal
            if (elements.clientDetailsModal) {
                elements.clientDetailsModal.classList.remove('hidden');
                initializeTabs();
            }

        } catch (error) {
            Logger.error('Error al cargar detalles del cliente:', error);
            showNotification('Error al cargar los detalles del cliente', 'error');
        }
    };

    window.closeModal = function(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) modal.classList.add('hidden');
    };

    window.confirmDelete = function(clientId) {
        if (elements.deleteConfirmModal) {
            window.clientToDelete = clientId;
            elements.deleteConfirmModal.classList.remove('hidden');
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
            Logger.error('Error al eliminar cliente:', error);
            showNotification(error.message, 'error');
        }
    };

    // Inicializar la aplicación
    initializeEventListeners();
    
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