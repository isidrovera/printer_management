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
    initializeDriverSelect(); // Cargar marca, modelo y driver dinámicamente
    initializeFormHandlers();
    initializeSearchFilter();
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

// Inicializar select de drivers (marca, modelo y archivo)
async function initializeDriverSelect() {
    const driverSelect = document.getElementById('driver');
    if (!driverSelect) return;

    try {
        // Hacer la petición al backend para obtener los drivers
        const response = await fetch('/api/v1/drivers'); // Endpoint para obtener drivers
        if (!response.ok) {
            throw new Error('Error al obtener la lista de drivers');
        }

        const drivers = await response.json();

        // Validar que la respuesta sea un array
        if (!Array.isArray(drivers)) {
            throw new Error('El formato de datos devuelto no es válido');
        }

        // Poblar el select con los drivers
        driverSelect.innerHTML = '<option value="">Seleccione un driver</option>';
        drivers.forEach((driver) => {
            const option = document.createElement('option');
            option.value = driver.id; // Asignar el ID del driver como valor
            option.textContent = `${driver.manufacturer} - ${driver.model} (${driver.driver_filename})`;
            driverSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error inicializando drivers:', error);
        showNotification('Error al cargar drivers', 'error');
    }
}

// Función para manejar formularios
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

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    // Implementa aquí tu lógica para mostrar notificaciones
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Función para cerrar modales
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('hidden');
        if (modalId === 'installPrinterModal') {
            document.getElementById('installPrinterForm').reset();
        }
    }
}

// Inicializar filtro de búsqueda
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
