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
    // Sistema de notificaciones
    const NotificationSystem = {
        container: document.getElementById('notification-container'),
        show: function(message, type = 'success', duration = 3000) {
            if (!this.container) return;

            const notification = document.createElement('div');
            notification.className = `transform transition-all duration-300 ease-in-out ${
                type === 'success' ? 'bg-green-500' :
                type === 'error' ? 'bg-red-500' :
                type === 'warning' ? 'bg-yellow-500' : 'bg-blue-500'
            } text-white px-6 py-3 rounded-lg shadow-lg`;

            // Agregar icono según el tipo
            const icon = document.createElement('i');
            icon.className = `fas ${
                type === 'success' ? 'fa-check-circle' :
                type === 'error' ? 'fa-exclamation-circle' :
                type === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle'
            } mr-2`;
            
            notification.appendChild(icon);
            notification.appendChild(document.createTextNode(message));
            
            // Agregar botón de cerrar
            const closeButton = document.createElement('button');
            closeButton.className = 'ml-3 text-white hover:text-gray-200 transition-colors';
            closeButton.innerHTML = '<i class="fas fa-times"></i>';
            closeButton.onclick = () => notification.remove();
            notification.appendChild(closeButton);

            this.container.appendChild(notification);

            // Animación de entrada
            requestAnimationFrame(() => {
                notification.style.transform = 'translateX(0)';
                notification.style.opacity = '1';
            });

            // Auto-eliminar después del tiempo especificado
            setTimeout(() => {
                notification.style.transform = 'translateX(100%)';
                notification.style.opacity = '0';
                setTimeout(() => notification.remove(), 300);
            }, duration);
        }
    };

    // Sistema de modales
    const ModalSystem = {
        show: function(modalId) {
            const modal = document.getElementById(modalId);
            if (!modal) return;
            
            modal.classList.remove('hidden');
            modal.setAttribute('aria-hidden', 'false');
            
            // Bloquear scroll del body
            document.body.style.overflow = 'hidden';
        },
        
        hide: function(modalId) {
            const modal = document.getElementById(modalId);
            if (!modal) return;
            
            modal.classList.add('hidden');
            modal.setAttribute('aria-hidden', 'true');
            
            // Restaurar scroll del body
            document.body.style.overflow = '';
        }
    };

    // Sistema de pestañas
    const TabSystem = {
        initialize: function() {
            const tabButtons = document.querySelectorAll('.tab-button');
            const tabContents = document.querySelectorAll('.tab-content');

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
                        if (content.id === `${tabName}Tab`) {
                            content.classList.remove('hidden');
                        } else {
                            content.classList.add('hidden');
                        }
                    });
                });
            });
        }
    };

    // Sistema de filtrado
    const FilterSystem = {
        elements: {
            searchInput: document.getElementById('searchInput'),
            statusFilter: document.getElementById('statusFilter'),
            typeFilter: document.getElementById('typeFilter')
        },

        initialize: function() {
            if (this.elements.searchInput) {
                this.elements.searchInput.addEventListener('input', () => this.filterClients());
            }
            if (this.elements.statusFilter) {
                this.elements.statusFilter.addEventListener('change', () => this.filterClients());
            }
            if (this.elements.typeFilter) {
                this.elements.typeFilter.addEventListener('change', () => this.filterClients());
            }
        },

        filterClients: function() {
            const searchTerm = this.elements.searchInput?.value?.toLowerCase() || '';
            const statusValue = this.elements.statusFilter?.value?.toLowerCase() || '';
            const typeValue = this.elements.typeFilter?.value?.toLowerCase() || '';

            const rows = document.querySelectorAll('tbody tr');
            let visibleCount = 0;

            rows.forEach(row => {
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
                if (isVisible) visibleCount++;
            });

            // Mostrar mensaje si no hay resultados
            const noResultsMessage = document.getElementById('noResultsMessage');
            if (noResultsMessage) {
                noResultsMessage.style.display = visibleCount === 0 ? 'block' : 'none';
            }
        }
    };

    // Sistema de detalles del cliente
    const ClientSystem = {
        // En tu ClientSystem.loadDetails
        loadDetails: async function(clientId) {
            try {
                const response = await fetch(`/clients/${clientId}/details`, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                if (!response.ok) {
                    if (response.status === 404) {
                        throw new Error('Cliente no encontrado');
                    }
                    throw new Error('Error al cargar los detalles');
                }
                
                const client = await response.json();
                
                // Actualizar campos básicos
                const fields = {
                    clientName: client.name,
                    businessName: client.business_name,
                    taxId: client.tax_id,
                    clientType: client.client_type,
                    clientStatus: client.status,
                    mainAddress: client.service_address,
                    mainCity: client.service_city,
                    mainState: client.service_state,
                    mainZipCode: client.service_zip_code,
                    mainCountry: client.service_country
                };

                Object.entries(fields).forEach(([id, value]) => {
                    const element = document.getElementById(id);
                    if (element) element.textContent = value || '';
                });

                // Actualizar contactos
                this.updateContactInfo('mainContactInfo', client.contact_info);
                this.updateContactInfo('technicalContactInfo', client.technical_contact_info);
                this.updateContactInfo('billingContactInfo', client.billing_contact_info);

                // Actualizar información del contrato
                this.updateContractInfo(client.contract_info);

                // Mostrar modal
                ModalSystem.show('clientDetailsModal');
                TabSystem.initialize();

            } catch (error) {
                NotificationSystem.show(error.message, 'error');
            }
        },

        updateContactInfo: function(containerId, contactInfo) {
            const container = document.getElementById(containerId);
            if (!container || !contactInfo) return;

            container.innerHTML = `
                <div class="space-y-2">
                    <div class="flex flex-col">
                        <span class="text-sm text-gray-500">Nombre</span>
                        <span class="text-base text-gray-900">${contactInfo.name || ''}</span>
                    </div>
                    <div class="flex flex-col">
                        <span class="text-sm text-gray-500">Email</span>
                        <span class="text-base text-gray-900">${contactInfo.email || ''}</span>
                    </div>
                    <div class="flex flex-col">
                        <span class="text-sm text-gray-500">Teléfono</span>
                        <span class="text-base text-gray-900">${contactInfo.phone || ''}</span>
                    </div>
                </div>
            `;
        },

        updateContractInfo: function(contractInfo) {
            if (!contractInfo) return;

            const elements = {
                contractNumber: contractInfo.number,
                contractStartDate: contractInfo.start_date,
                contractEndDate: contractInfo.end_date,
                serviceLevel: contractInfo.service_level,
                paymentTerms: contractInfo.payment_terms,
                creditLimit: contractInfo.credit_limit,
                currentBalance: contractInfo.current_balance,
                pendingInvoices: contractInfo.pending_invoices,
                lastPayment: contractInfo.last_payment
            };

            Object.entries(elements).forEach(([id, value]) => {
                const element = document.getElementById(id);
                if (element) element.textContent = value || '';
            });
        },

        delete: async function(clientId) {
            try {
                const response = await fetch(`/clients/${clientId}`, {
                    method: 'DELETE',
                    headers: { 'Content-Type': 'application/json' }
                });

                const data = await response.json();

                if (data.success) {
                    NotificationSystem.show('Cliente eliminado con éxito', 'success');
                    const row = document.querySelector(`tr[data-client-id="${clientId}"]`);
                    if (row) {
                        row.style.animation = 'fadeOut 0.3s ease';
                        setTimeout(() => row.remove(), 300);
                    }
                    ModalSystem.hide('deleteConfirmModal');
                } else {
                    throw new Error(data.error || 'Error al eliminar el cliente');
                }
            } catch (error) {
                NotificationSystem.show(error.message, 'error');
            }
        }
    };

    // Funciones globales
    window.showClientDetails = function(clientId) {
        ClientSystem.loadDetails(clientId);
    };

    window.closeModal = function(modalId) {
        ModalSystem.hide(modalId);
    };

    window.confirmDelete = function(clientId) {
        window.clientToDelete = clientId;
        ModalSystem.show('deleteConfirmModal');
    };

    window.executeDelete = function() {
        const clientId = window.clientToDelete;
        if (clientId) ClientSystem.delete(clientId);
    };

    // Inicialización
    FilterSystem.initialize();
    TabSystem.initialize();

    // Estilos de animación
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeOut {
            from { opacity: 1; transform: translateY(0); }
            to { opacity: 0; transform: translateY(-10px); }
        }

        .notification-enter {
            transform: translateX(100%);
            opacity: 0;
        }

        .notification-enter-active {
            transform: translateX(0);
            opacity: 1;
            transition: transform 300ms ease-out, opacity 300ms ease-out;
        }

        .notification-exit {
            transform: translateX(0);
            opacity: 1;
        }

        .notification-exit-active {
            transform: translateX(100%);
            opacity: 0;
            transition: transform 300ms ease-in, opacity 300ms ease-in;
        }
    `;
    document.head.appendChild(style);
});