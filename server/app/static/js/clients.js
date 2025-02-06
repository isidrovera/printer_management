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

    // Referencias a elementos DOM
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    const typeFilter = document.getElementById('typeFilter');
    const notificationContainer = document.getElementById('notification-container');
    const clientDetailsModal = document.getElementById('clientDetailsModal');
    const deleteConfirmModal = document.getElementById('deleteConfirmModal');

    // Verificación de elementos críticos
    if (!searchInput) Logger.warn('Elemento searchInput no encontrado');
    if (!statusFilter) Logger.warn('Elemento statusFilter no encontrado');
    if (!typeFilter) Logger.warn('Elemento typeFilter no encontrado');
    if (!notificationContainer) Logger.warn('Elemento notificationContainer no encontrado');
    if (!clientDetailsModal) Logger.warn('Elemento clientDetailsModal no encontrado');
    if (!deleteConfirmModal) Logger.warn('Elemento deleteConfirmModal no encontrado');

    // Función para mostrar notificaciones
    function showNotification(message, type = 'success') {
        Logger.info(`Mostrando notificación: ${message} (tipo: ${type})`);
        
        const notification = document.createElement('div');
        notification.className = `${type === 'success' ? 'bg-green-500' : 'bg-red-500'} text-white px-6 py-3 rounded-lg shadow-lg transition-opacity duration-300`;
        notification.textContent = message;
        
        if (notificationContainer) {
            notificationContainer.appendChild(notification);
            Logger.debug('Notificación agregada al contenedor');

            setTimeout(() => {
                notification.style.opacity = '0';
                setTimeout(() => {
                    notification.remove();
                    Logger.debug('Notificación removida');
                }, 300);
            }, 3000);
        } else {
            Logger.error('No se pudo mostrar la notificación: contenedor no encontrado');
        }
    }

    // Función de búsqueda y filtrado
    function filterClients() {
        Logger.debug('Iniciando filtrado de clientes');
        
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

    // Event listeners para búsqueda y filtros
    if (searchInput) {
        searchInput.addEventListener('input', () => {
            Logger.debug('Evento input en searchInput');
            filterClients();
        });
    }

    if (statusFilter) {
        statusFilter.addEventListener('change', () => {
            Logger.debug('Evento change en statusFilter');
            filterClients();
        });
    }

    if (typeFilter) {
        typeFilter.addEventListener('change', () => {
            Logger.debug('Evento change en typeFilter');
            filterClients();
        });
    }

    // Manejo de tabs en el modal de detalles
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    Logger.debug(`Encontrados: ${tabButtons.length} botones de tab y ${tabContents.length} contenidos de tab`);

    if (tabButtons.length && tabContents.length) {
        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const tabName = button.getAttribute('data-tab');
                Logger.debug(`Cambiando a tab: ${tabName}`);

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
                        Logger.debug(`Mostrando contenido de tab: ${content.id}`);
                    } else {
                        content.classList.add('hidden');
                    }
                });
            });
        });
    }

    // Funciones globales
    window.showClientDetails = async function(clientId) {
        Logger.info(`Cargando detalles del cliente: ${clientId}`);
        
        try {
            const response = await fetch(`/clients/${clientId}/details`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const client = await response.json();
            Logger.debug('Datos del cliente recibidos:', client);

            // Actualizar campos del modal
            const fields = {
                'clientName': client.name,
                'businessName': client.business_name,
                'taxId': client.tax_id,
                'clientType': client.client_type
            };

            Object.entries(fields).forEach(([elementId, value]) => {
                const element = document.getElementById(elementId);
                if (element) {
                    element.textContent = value;
                } else {
                    Logger.warn(`Elemento ${elementId} no encontrado`);
                }
            });

            // Actualizar estado
            const statusElement = document.getElementById('clientStatus');
            if (statusElement) {
                statusElement.textContent = client.status;
                const statusClasses = {
                    'activo': 'bg-green-100 text-green-800',
                    'inactivo': 'bg-red-100 text-red-800',
                    'default': 'bg-gray-100 text-gray-800'
                };
                statusElement.className = `px-3 py-1 rounded-full text-sm font-medium ${
                    statusClasses[client.status] || statusClasses.default
                }`;
            }

            // Actualizar botón de edición
            const editButton = document.getElementById('editClientButton');
            if (editButton) {
                editButton.href = `/clients/${clientId}/edit`;
            }

            // Mostrar modal
            if (clientDetailsModal) {
                clientDetailsModal.classList.remove('hidden');
                Logger.info('Modal de detalles mostrado exitosamente');
            } else {
                Logger.error('Modal de detalles no encontrado');
            }

        } catch (error) {
            Logger.error('Error cargando detalles del cliente:', error);
            showNotification('Error al cargar los detalles del cliente', 'error');
        }
    };

    window.closeModal = function(modalId) {
        Logger.debug(`Cerrando modal: ${modalId}`);
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('hidden');
            Logger.debug('Modal cerrado exitosamente');
        } else {
            Logger.warn(`Modal ${modalId} no encontrado`);
        }
    };

    window.confirmDelete = function(clientId) {
        Logger.debug(`Iniciando confirmación de eliminación para cliente: ${clientId}`);
        if (deleteConfirmModal) {
            window.clientToDelete = clientId;
            deleteConfirmModal.classList.remove('hidden');
            Logger.info('Modal de confirmación de eliminación mostrado');
        } else {
            Logger.error('Modal de confirmación de eliminación no encontrado');
        }
    };

    window.executeDelete = async function() {
        const clientId = window.clientToDelete;
        if (!clientId) {
            Logger.error('No se encontró ID de cliente para eliminar');
            return;
        }

        Logger.info(`Iniciando eliminación del cliente: ${clientId}`);

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
                    setTimeout(() => {
                        row.remove();
                        Logger.debug('Fila de cliente removida del DOM');
                    }, 300);
                }
                
                closeModal('deleteConfirmModal');
            } else {
                Logger.error('Error en la respuesta al eliminar cliente:', data.error);
                showNotification(data.error || 'Error al eliminar el cliente', 'error');
            }
        } catch (error) {
            Logger.error('Error durante la eliminación del cliente:', error);
            showNotification('Error al eliminar el cliente', 'error');
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