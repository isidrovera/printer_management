// static/js/agents.js

// Variables globales
let currentAgentToken = '';
let agentToDelete = null;

// WebSocket para actualizaciones en tiempo real
let ws;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    initializeWebSocket();
    initializeSearchFilter();
    initializeFormHandlers();
});

// Función para mostrar el modal de instalación de impresora
function showInstallPrinter(agentToken) {
    currentAgentToken = agentToken;
    const modal = document.getElementById('installPrinterModal');
    if (modal) {
        modal.classList.remove('hidden');
        // Resetear el formulario
        document.getElementById('installPrinterForm').reset();
        // Actualizar el token oculto
        const tokenInput = document.getElementById('agentToken');
        if (tokenInput) {
            tokenInput.value = agentToken;
        }
    }
}

// Función para mostrar el modal de confirmación de eliminación
function confirmDelete(agentId) {
    agentToDelete = agentId;
    const modal = document.getElementById('deleteConfirmModal');
    if (modal) {
        modal.classList.remove('hidden');
    }
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

// Función para eliminar un agente
async function deleteAgent() {
    if (!agentToDelete) return;

    try {
        const response = await fetch(`/api/v1/agents/${agentToDelete}`, {
            method: 'DELETE',
        });

        if (response.ok) {
            showNotification('Agente eliminado correctamente', 'success');
            // Recargar la página después de un breve retraso
            setTimeout(() => window.location.reload(), 1000);
        } else {
            const data = await response.json();
            throw new Error(data.detail || 'Error al eliminar el agente');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
    } finally {
        closeModal('deleteConfirmModal');
        agentToDelete = null;
    }
}

// Inicializar manejadores de formularios
function initializeFormHandlers() {
    // Manejar el envío del formulario de instalación
    const installForm = document.getElementById('installPrinterForm');
    if (installForm) {
        installForm.addEventListener('submit', async function(e) {
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

    // Manejar cambios en el selector de fabricante
    const manufacturerSelect = document.getElementById('manufacturer');
    if (manufacturerSelect) {
        manufacturerSelect.addEventListener('change', loadModels);
    }
}

// Cargar modelos según el fabricante seleccionado
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
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
}

// Inicializar WebSocket
function initializeWebSocket() {
    connectWebSocket();
}

// Conectar WebSocket
function connectWebSocket() {
    ws = new WebSocket(`ws://${window.location.host}/ws/api/v1/ws/status`);
    
    ws.onopen = () => {
        console.log('WebSocket conectado');
        reconnectAttempts = 0;
    };

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            handleWebSocketMessage(data);
        } catch (error) {
            console.error('Error parsing WebSocket message:', error);
        }
    };

    ws.onclose = () => {
        console.log('WebSocket desconectado');
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            console.log(`Reintentando conexión ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}`);
            setTimeout(connectWebSocket, 1000 * reconnectAttempts);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
}

// Manejar mensajes del WebSocket
function handleWebSocketMessage(data) {
    if (data.type === 'status_update') {
        updateAgentStatus(data.agent_id, data.status);
    } else if (data.type === 'installation_status') {
        handleInstallationStatus(data);
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
                // Actualizar clases y texto
                statusSpan.className = `inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    status === 'online' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`;
                const indicator = statusSpan.querySelector('span');
                if (indicator) {
                    indicator.className = `w-2 h-2 mr-2 rounded-full ${
                        status === 'online' ? 'bg-green-400' : 'bg-red-400'
                    }`;
                }
                statusSpan.lastChild.textContent = status.charAt(0).toUpperCase() + status.slice(1);
            }
        }

        // Actualizar botón de instalación
        const installButton = row.querySelector('button[onclick^="showInstallPrinter"]');
        if (installButton) {
            if (status === 'online') {
                installButton.removeAttribute('disabled');
                installButton.classList.remove('opacity-50', 'cursor-not-allowed');
            } else {
                installButton.setAttribute('disabled', '');
                installButton.classList.add('opacity-50', 'cursor-not-allowed');
            }
        }
    }
}

// Manejar estado de instalación
function handleInstallationStatus(data) {
    const status = data.success ? 'success' : 'error';
    showNotification(data.message, status);
}