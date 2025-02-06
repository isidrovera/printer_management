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

// Función para agregar event listener de forma segura
function addSafeEventListener(elementId, event, handler) {
    const element = document.getElementById(elementId);
    if (element) {
        element.addEventListener(event, handler);
        Logger.debug(`Event listener agregado a ${elementId}`);
    } else {
        Logger.warn(`Elemento ${elementId} no encontrado para event listener`);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    Logger.info('Iniciando aplicación de gestión de clientes');

    // Filtrado y búsqueda
    function filterClients() {
        Logger.debug('Iniciando filtrado de clientes');
        const searchInput = document.getElementById('searchInput');
        const statusFilter = document.getElementById('statusFilter');
        const typeFilter = document.getElementById('typeFilter');
        
        const searchTerm = searchInput?.value?.toLowerCase() || '';
        const statusValue = statusFilter?.value?.toLowerCase() || '';
        const typeValue = typeFilter?.value?.toLowerCase() || '';
        
        Logger.debug('Términos de búsqueda:', { searchTerm, statusValue, typeValue });

        const rows = document.querySelectorAll('tbody tr');
        Logger.debug(`Encontradas ${rows.length} filas para filtrar`);

        let visibleRows = 0;
        rows.forEach((row, index) => {
            try {
                const text = row.textContent.toLowerCase();
                const statusCell = row.querySelector('td:nth-child(5)');
                const typeCell = row.querySelector('td:nth-child(3)');
                
                const status = statusCell?.textContent?.toLowerCase().trim() || '';
                const type = typeCell?.textContent?.toLowerCase().trim() || '';

                const matchesSearch = text.includes(searchTerm);
                const matchesStatus = statusValue === '' || status.includes(statusValue);
                const matchesType = typeValue === '' || type.includes(typeValue);

                const isVisible = matchesSearch && matchesStatus && matchesType;
                row.style.display = isVisible ? '' : 'none';
                
                if (isVisible) visibleRows++;
                
            } catch (error) {
                Logger.error(`Error al filtrar fila ${index}:`, error);
                row.style.display = '';
                visibleRows++;
            }
        });

        Logger.info(`Filtrado completado: ${visibleRows} filas visibles de ${rows.length} totales`);
    }

    // Agregar event listeners de manera segura
    addSafeEventListener('searchInput', 'input', filterClients);
    addSafeEventListener('statusFilter', 'change', filterClients);
    addSafeEventListener('typeFilter', 'change', filterClients);

    // Funciones para modales
    window.showNotification = function(message, type = 'success') {
        Logger.info(`Mostrando notificación: ${message} (tipo: ${type})`);
        const container = document.getElementById('notification-container');
        if (!container) {
            Logger.error('Contenedor de notificaciones no encontrado');
            return;
        }

        const notification = document.createElement('div');
        notification.className = `${type === 'success' ? 'bg-green-500' : 'bg-red-500'} text-white px-6 py-3 rounded-lg shadow-lg transition-opacity duration-300`;
        notification.textContent = message;
        container.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    window.showClientDetails = async function(clientId) {
        Logger.info(`Cargando detalles del cliente: ${clientId}`);
        const modal = document.getElementById('clientDetailsModal');
        
        if (!modal) {
            Logger.error('Modal de detalles no encontrado');
            return;
        }

        try {
            const response = await fetch(`/clients/${clientId}/details`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const client = await response.json();
            Logger.debug('Datos del cliente recibidos:', client);

            // Actualizar información básica
            updateElementText('clientName', client.name);
            updateElementText('businessName', client.business_name);
            updateElementText('taxId', client.tax_id);
            updateElementText('clientType', client.client_type);
            
            // Actualizar el enlace de edición
            const editButton = document.getElementById('editClientButton');
            if (editButton) {
                editButton.href = `/clients/${clientId}/edit`;
            }

            modal.classList.remove('hidden');
            initializeTabs();

        } catch (error) {
            Logger.error('Error cargando detalles del cliente:', error);
            showNotification('Error al cargar los detalles del cliente', 'error');
        }
    };

    function updateElementText(elementId, text) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text || '';
        } else {
            Logger.warn(`Elemento ${elementId} no encontrado`);
        }
    }

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

    window.closeModal = function(modalId) {
        Logger.debug(`Cerrando modal: ${modalId}`);
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
        }
    };

    window.confirmDelete = function(clientId) {
        Logger.debug(`Iniciando confirmación de eliminación para cliente: ${clientId}`);
        const modal = document.getElementById('deleteConfirmModal');
        if (modal) {
            window.clientToDelete = clientId;
            modal.classList.remove('hidden');
        }
    };

    window.executeDelete = async function() {
        const clientId = window.clientToDelete;
        if (!clientId) {
            Logger.error('No se encontró ID de cliente para eliminar');
            return;
        }

        try {
            const response = await fetch(`/clients/${clientId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                Logger.info(`Cliente ${clientId} eliminado exitosamente`);
                showNotification('Cliente eliminado con éxito');
                
                const row = document.querySelector(`tr[data-client-id="${clientId}"]`);
                if (row) {
                    row.style.animation = 'fadeOut 0.3s ease';
                    setTimeout(() => row.remove(), 300);
                }
                
                closeModal('deleteConfirmModal');
            } else {
                throw new Error(data.error || 'Error desconocido');
            }
        } catch (error) {
            Logger.error('Error durante la eliminación del cliente:', error);
            showNotification(error.message || 'Error al eliminar el cliente', 'error');
        }
    };

    // Agregar estilos de animación
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeOut {
            from { opacity: 1; transform: translateY(0); }
            to { opacity: 0; transform: translateY(-10px); }
        }
    `;
    document.head.appendChild(style);
    
    Logger.info('Aplicación de gestión de clientes inicializada completamente');
});