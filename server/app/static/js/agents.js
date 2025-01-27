// static/js/agents.js

// Variables globales
let currentAgentToken = '';
let agentToDelete = null;

// WebSocket para actualizaciones en tiempo real
let ws;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// Configuración WebSocket
const WS_CONFIG = {
    url: `ws://${window.location.host}/ws/status`,
    reconnectInterval: 1000,
    maxReconnectAttempts: 5
};

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function () {
    initializeWebSocket(); // Llamada corregida y consistente
    initializeSearchFilter();
    initializeFormHandlers();
    initializeManufacturerSelect();
});

// Función para inicializar el WebSocket
function initializeWebSocket() {
    try {
        console.log('Intentando conectar WebSocket a:', WS_CONFIG.url);
        ws = new WebSocket(WS_CONFIG.url);
        
        ws.onopen = () => {
            console.log('WebSocket conectado exitosamente');
            reconnectAttempts = 0;
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('Mensaje recibido:', data);
                handleWebSocketMessage(data);
            } catch (error) {
                console.error('Error al procesar mensaje:', error);
            }
        };

        ws.onclose = (event) => {
            console.log('WebSocket desconectado. Código:', event.code, 'Razón:', event.reason);
            if (reconnectAttempts < WS_CONFIG.maxReconnectAttempts) {
                reconnectAttempts++;
                console.log(`Reintentando conexión ${reconnectAttempts}/${WS_CONFIG.maxReconnectAttempts}`);
                setTimeout(initializeWebSocket, WS_CONFIG.reconnectInterval * reconnectAttempts);
            } else {
                console.log('Número máximo de intentos de reconexión alcanzado');
                showNotification('Se perdió la conexión con el servidor', 'error');
            }
        };

        ws.onerror = (error) => {
            console.error('Error en WebSocket:', error);
        };
    } catch (error) {
        console.error('Error al crear conexión WebSocket:', error);
        showNotification('Error al conectar con el servidor', 'error');
    }
}

// Manejar mensajes del WebSocket
function handleWebSocketMessage(data) {
    if (data.type === 'status_update') {
        updateAgentStatus(data.agent_id, data.status);
    } else if (data.type === 'printer_installation_status') {
        handlePrinterInstallationStatus(data);
    }
}

// Manejar estado de instalación de impresora
function handlePrinterInstallationStatus(data) {
    const status = data.success ? 'success' : 'error';
    showNotification(data.message, status);
}

// Inicializar manejadores de formularios
function initializeFormHandlers() {
    const installForm = document.getElementById('installPrinterForm');
    if (installForm) {
        installForm.addEventListener('submit', async function (e) {
            e.preventDefault();

            const manufacturer = document.getElementById('manufacturer').value;
            const model = document.getElementById('model').value;
            const printerIp = document.getElementById('printerIp').value;

            if (!manufacturer || !model || !printerIp) {
                showNotification('Por favor complete todos los campos', 'error');
                return;
            }

            try {
                const response = await fetch(`/api/v1/printers/install/${currentAgentToken}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        printer_ip: printerIp,
                        manufacturer: manufacturer,
                        model: model
                    })
                });

                const data = await response.json();

                if (response.ok) {
                    showNotification('Comando de instalación enviado correctamente', 'success');
                    closeModal('installPrinterModal');
                } else {
                    throw new Error(data.detail || 'Error al enviar el comando de instalación');
                }
            } catch (error) {
                console.error('Error:', error);
                showNotification(error.message, 'error');
            }
        });
    }
}

// Inicializar select de fabricantes
async function initializeManufacturerSelect() {
    const manufacturerSelect = document.getElementById('manufacturer');
    if (!manufacturerSelect) return;

    try {
        const response = await fetch('/api/v1/printers/manufacturers');
        const manufacturers = await response.json();

        manufacturerSelect.innerHTML = '<option value="">Seleccione un fabricante</option>';
        manufacturers.forEach(manufacturer => {
            const option = document.createElement('option');
            option.value = manufacturer;
            option.textContent = manufacturer;
            manufacturerSelect.appendChild(option);
        });

        manufacturerSelect.addEventListener('change', loadModels);
    } catch (error) {
        console.error('Error cargando fabricantes:', error);
        showNotification('Error al cargar fabricantes', 'error');
    }
}

// Cargar modelos según fabricante
async function loadModels(e) {
    const manufacturer = e.target.value;
    const modelSelect = document.getElementById('model');

    if (!modelSelect) return;

    modelSelect.disabled = true;
    modelSelect.innerHTML = '<option value="">Cargando modelos...</option>';

    if (!manufacturer) {
        modelSelect.innerHTML = '<option value="">Seleccione un modelo</option>';
        modelSelect.disabled = false;
        return;
    }

    try {
        const response = await fetch(`/api/v1/printers/models/${manufacturer}`);
        const models = await response.json();

        modelSelect.innerHTML = '<option value="">Seleccione un modelo</option>';
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            modelSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error:', error);
        showNotification('Error al cargar los modelos', 'error');
        modelSelect.innerHTML = '<option value="">Error al cargar modelos</option>';
    } finally {
        modelSelect.disabled = false;
    }
}

// Inicializar filtro de búsqueda
function initializeSearchFilter() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function (e) {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
}

// Actualizar estado del agente en la UI
function updateAgentStatus(agentId, status) {
    const row = document.querySelector(`tr[data-agent-id="${agentId}"]`);
    if (row) {
        const statusCell = row.querySelector('td:nth-child(6)');
        if (statusCell) {
            const statusSpan = statusCell.querySelector('span');
            if (statusSpan) {
                statusSpan.className = `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    status === 'online' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`;
                statusSpan.lastChild.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            }
        }
    }
}
