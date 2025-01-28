// static/js/agents.js

// Variables globales
let currentAgentToken = '';
let agentToDelete = null;

// Configuración WebSocket
const WS_CONFIG = {
    url: `ws://${window.location.host}/ws/status`,
    reconnectInterval: 1000,
    maxReconnectAttempts: 5
};

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function () {
    initializeWebSocket();
    initializeSearchFilter();
    initializeFormHandlers();
    initializeDriverSelect(); // Añadido para cargar drivers al inicio
});

// Inicializar WebSocket
function initializeWebSocket() {
    try {
        console.log('Intentando conectar WebSocket a:', WS_CONFIG.url);
        const ws = new WebSocket(WS_CONFIG.url);

        ws.onopen = () => {
            console.log('WebSocket conectado exitosamente');
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('Mensaje recibido:', data);
                // Maneja los datos según el tipo
            } catch (error) {
                console.error('Error al procesar mensaje:', error);
            }
        };

        ws.onclose = (event) => {
            console.warn('WebSocket cerrado. Código:', event.code);
        };

        ws.onerror = (error) => {
            console.error('Error en WebSocket:', error);
        };
    } catch (error) {
        console.error('Error al crear conexión WebSocket:', error);
    }
}

// Función para inicializar el filtro de búsqueda
function initializeSearchFilter() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function (e) {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');

            rows.forEach((row) => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
}

// Función para inicializar manejadores de formularios
function initializeFormHandlers() {
    const installForm = document.getElementById('installPrinterForm');
    if (installForm) {
        installForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const driverId = document.getElementById('driver').value;
            const printerIp = document.getElementById('printerIp').value;

            if (!driverId || !printerIp) {
                showNotification('Por favor complete todos los campos', 'error');
                return;
            }

            try {
                const response = await fetch(`/api/v1/printers/install/${currentAgentToken}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        printer_ip: printerIp,
                        driver_id: driverId
                    }),
                });

                const data = await response.json();
                if (response.ok) {
                    showNotification('Comando de instalación enviado correctamente', 'success');
                    closeModal('installPrinterModal');
                } else {
                    throw new Error(data.detail || 'Error al enviar el comando de instalación');
                }
            } catch (error) {
                console.error('Error al enviar formulario:', error);
                showNotification(error.message, 'error');
            }
        });
    }
}

// Función para inicializar el select de drivers
// Función para inicializar el select de drivers
async function initializeDriverSelect() {
    const driverSelect = document.getElementById('driver');
    if (!driverSelect) return;

    try {
        console.group('Carga de Drivers');
        console.log('Intentando cargar drivers...');
        
        // Actualizamos la URL para usar la nueva ruta API
        const response = await fetch('/api/v1/drivers', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });

        console.log('Respuesta de drivers:', {
            status: response.status,
            headers: Object.fromEntries(response.headers.entries())
        });

        if (!response.ok) {
            const text = await response.text();
            console.error('Contenido de respuesta:', text);
            throw new Error(`Error al obtener drivers. Status: ${response.status}`);
        }

        const drivers = await response.json();
        
        if (!Array.isArray(drivers)) {
            throw new Error('El formato de datos devuelto no es válido');
        }

        console.log('Drivers recuperados:', drivers);

        // Poblar el select con los drivers
        driverSelect.innerHTML = '<option value="">Seleccione un driver</option>';
        drivers.forEach((driver) => {
            const option = document.createElement('option');
            option.value = driver.id;
            option.textContent = `${driver.manufacturer} - ${driver.model} (${driver.driver_filename})`;
            driverSelect.appendChild(option);
        });

        console.log('Select de drivers poblado exitosamente');
        console.groupEnd();

    } catch (error) {
        console.groupEnd();
        console.error('Error completo inicializando drivers:', error);
        showNotification(`Error al cargar drivers: ${error.message}`, 'error');
    }
}
// Función para mostrar el modal de instalación de impresora
function showInstallPrinter(agentToken) {
    currentAgentToken = agentToken;

    const modal = document.getElementById('installPrinterModal');
    if (modal) {
        modal.classList.remove('hidden');
        document.getElementById('installPrinterForm').reset(); // Resetear el formulario
        initializeDriverSelect(); // Llenar el select de drivers
    } else {
        console.warn("El modal no existe en el DOM.");
    }
}

// Función para cerrar un modal por ID
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        if (modalId === 'installPrinterModal') {
            document.getElementById('installPrinterForm').reset();
        }
    }
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Implementación de notificación visual
    const notificationContainer = document.getElementById('notification-container');
    if (notificationContainer) {
        // Crear elemento de notificación
        const notification = document.createElement('div');
        notification.classList.add('notification', `notification-${type}`);
        notification.innerHTML = `
            <strong>${type.toUpperCase()}:</strong> 
            ${message}
            <button class="close-notification">&times;</button>
        `;

        // Añadir evento de cierre
        const closeButton = notification.querySelector('.close-notification');
        closeButton.addEventListener('click', () => {
            notification.remove();
        });

        notificationContainer.appendChild(notification);

        // Eliminar la notificación después de unos segundos
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                notification.remove();
            }, 500);
        }, 5000);
    }
}