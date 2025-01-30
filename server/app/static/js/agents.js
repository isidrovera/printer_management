// static/js/agents.js

// Variables globales
let currentAgentToken = '';
let agentToDelete = null;

// Configuración WebSocket
const WS_CONFIG = {
    url: `ws://${window.location.host}/api/v1/ws/status`,
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
        let reconnectAttempts = 0;

        ws.onopen = () => {
            console.log('WebSocket conectado exitosamente');
            reconnectAttempts = 0; // Reiniciar contador de intentos al conectar exitosamente
            showNotification('Conexión establecida con el servidor', 'success');
        };

        ws.onmessage = (event) => {
            try {
                // Verificar si event.data es una cadena válida
                if (typeof event.data !== 'string') {
                    throw new Error('Datos recibidos en formato no válido');
                }

                // Intentar parsear el JSON con manejo de errores más detallado
                let data;
                try {
                    data = JSON.parse(event.data);
                } catch (parseError) {
                    console.error('Error al parsear JSON:', {
                        error: parseError,
                        rawData: event.data.slice(0, 100) + '...' // Mostrar los primeros 100 caracteres
                    });
                    throw parseError;
                }

                // Procesar los diferentes tipos de mensajes
                switch (data.type) {
                    case 'agent_status':
                        updateAgentStatus(data);
                        break;
                    case 'printer_status':
                        updatePrinterStatus(data);
                        break;
                    case 'error':
                        handleErrorMessage(data);
                        break;
                    default:
                        console.log('Mensaje recibido sin tipo específico:', data);
                }

            } catch (error) {
                console.error('Error al procesar mensaje:', {
                    errorType: error.name,
                    errorMessage: error.message,
                    stack: error.stack
                });
                showNotification('Error al procesar mensaje del servidor', 'error');
            }
        };

        ws.onclose = (event) => {
            console.warn('WebSocket cerrado. Código:', event.code);
            showNotification('Conexión perdida con el servidor', 'warning');

            // Intentar reconectar si no excedimos el límite de intentos
            if (reconnectAttempts < WS_CONFIG.maxReconnectAttempts) {
                reconnectAttempts++;
                console.log(`Intento de reconexión ${reconnectAttempts} de ${WS_CONFIG.maxReconnectAttempts}`);
                setTimeout(() => {
                    initializeWebSocket();
                }, WS_CONFIG.reconnectInterval);
            } else {
                showNotification('No se pudo restablecer la conexión con el servidor', 'error');
            }
        };

        ws.onerror = (error) => {
            console.error('Error en WebSocket:', error);
            showNotification('Error en la conexión con el servidor', 'error');
        };

        return ws;

    } catch (error) {
        console.error('Error al crear conexión WebSocket:', error);
        showNotification('Error al crear la conexión con el servidor', 'error');
    }
}


// Funciones auxiliares para manejar diferentes tipos de mensajes
function updateAgentStatus(data) {
    try {
        // Actualizar el estado del agente en la interfaz
        const agentElement = document.querySelector(`[data-agent-id="${data.agent_id}"]`);
        if (agentElement) {
            // Actualizar el estado visual del agente
            const statusElement = agentElement.querySelector('.agent-status');
            if (statusElement) {
                statusElement.className = `agent-status status-${data.status}`;
                statusElement.textContent = data.status;
            }
        }
    } catch (error) {
        console.error('Error al actualizar estado del agente:', error);
    }
}

function updatePrinterStatus(data) {
    try {
        // Actualizar el estado de la impresora en la interfaz
        const printerElement = document.querySelector(`[data-printer-id="${data.printer_id}"]`);
        if (printerElement) {
            // Actualizar el estado visual de la impresora
            const statusElement = printerElement.querySelector('.printer-status');
            if (statusElement) {
                statusElement.className = `printer-status status-${data.status}`;
                statusElement.textContent = data.status;
            }
        }
    } catch (error) {
        console.error('Error al actualizar estado de la impresora:', error);
    }
}

function handleErrorMessage(data) {
    console.error('Error recibido del servidor:', data.error);
    showNotification(data.error.message || 'Error del servidor', 'error');
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
    // Actualizar la función de envío del formulario en initializeFormHandlers
    if (installForm) {
        installForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            try {
                const driverId = document.getElementById('driver').value;
                const printerIp = document.getElementById('printerIp').value;

                if (!driverId || !printerIp) {
                    showNotification('Por favor complete todos los campos', 'error');
                    return;
                }

                console.log('Enviando solicitud de instalación:', {
                    printer_ip: printerIp,
                    driver_id: parseInt(driverId)
                });

                const response = await fetch(`/api/v1/printers/install/${currentAgentToken}`, {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({
                        printer_ip: printerIp,
                        driver_id: parseInt(driverId)
                    })
                });

                // Mejorar el manejo de errores
                if (!response.ok) {
                    const errorData = await response.json();
                    console.error('Error response:', errorData);
                    throw new Error(errorData.detail || `Error en la instalación: ${response.status}`);
                }

                const data = await response.json();
                console.log('Respuesta exitosa:', data);
                showNotification('Comando de instalación enviado correctamente', 'success');
                closeModal('installPrinterModal');

            } catch (error) {
                console.error('Error detallado:', error);
                showNotification(`Error al instalar impresora: ${error.message}`, 'error');
            }
        });
    }
}


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