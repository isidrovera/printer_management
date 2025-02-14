// static/js/agents.js
// PARTE 1: Variables Globales y Funciones Base

// Variables globales
let currentAgentToken = '';
let agentToDelete = null;
let wsConnection = null;
let reconnectAttempts = 0;

// Funciones de utilidad para URLs
function getSecureBaseUrl() {
    return `${window.location.protocol}//${window.location.host}`;
}

function getWebSocketUrl(path) {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    return `${protocol}//${host}${path}`;
}

// Configuración WebSocket
const WS_CONFIG = {
    url: getWebSocketUrl('/api/v1/ws/status'),
    reconnectInterval: 1000,
    maxReconnectAttempts: 10,
    currentInstallation: null
};

// Función para manejar mensajes del WebSocket
function handleWebSocketMessage(event) {
    console.group('Mensaje WebSocket Recibido');
    console.log('Mensaje raw:', event.data);

    try {
        // Verificar si es un mensaje de log del agente
        if (typeof event.data === 'string' && event.data.startsWith('Agent')) {
            console.log('📝 Mensaje de log del agente:', event.data);
            handleAgentLogMessage(event.data);
            console.groupEnd();
            return;
        }

        // Intentar parsear como JSON
        let data;
        try {
            data = JSON.parse(event.data);
            console.log('✅ JSON parseado correctamente:', data);
        } catch (parseError) {
            console.warn('⚠️ No se pudo parsear como JSON:', {
                error: parseError,
                rawData: event.data.slice(0, 100) + (event.data.length > 100 ? '...' : '')
            });
            handleAgentLogMessage(event.data);
            console.groupEnd();
            return;
        }

        // Procesar mensaje JSON según su tipo
        if (data && data.type) {
            console.log(`🔄 Procesando mensaje de tipo: ${data.type}`);
            processJsonMessage(data);
        } else {
            console.log('ℹ️ Mensaje JSON sin tipo específico:', data);
        }

    } catch (error) {
        console.error('❌ Error procesando mensaje:', error);
        addLogMessage('Error al procesar mensaje: ' + error.message, 'error');
    }
    console.groupEnd();
}

// Función para actualizar la información del agente en el DOM
function updateAgentInfoContent(agentInfo) {
    const content = document.getElementById('agentInfoContent');
    if (!content) return;
    
    content.innerHTML = `
        <div class="p-4">
            <h3 class="text-lg font-bold mb-4">Información del Agente</h3>
            <div class="grid grid-cols-2 gap-4">
                <div>
                    <p><strong>Hostname:</strong> ${agentInfo.hostname}</p>
                    <p><strong>Username:</strong> ${agentInfo.username}</p>
                    <p><strong>IP:</strong> ${agentInfo.ip_address}</p>
                </div>
                <div>
                    <p><strong>Tipo:</strong> ${agentInfo.device_type}</p>
                    <p><strong>Estado:</strong> ${agentInfo.status}</p>
                    <p><strong>Token:</strong> ${agentInfo.token}</p>
                </div>
            </div>
        </div>
    `;
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
    try {
        console.group('Inicialización de la Aplicación');
        console.log('Iniciando componentes principales');
        
        initializeWebSocket();
        initializeSearchFilter();
        initializeFormHandlers();
        initializeDriverSelect();
        
        console.log('Componentes principales inicializados correctamente');
        console.groupEnd();
    } catch (error) {
        console.error('Error en la inicialización:', error);
        showNotification('Error al inicializar la aplicación', 'error');
    }
});
// PARTE 2: WebSocket y Manejo de Mensajes

// Inicializar WebSocket
function initializeWebSocket() {
    try {
        console.group('Inicialización WebSocket');
        console.log('Intentando conectar WebSocket a:', WS_CONFIG.url);
        
        if (wsConnection) {
            wsConnection.close();
        }

        wsConnection = new WebSocket(WS_CONFIG.url);

        wsConnection.onopen = () => {
            console.log('✅ WebSocket conectado exitosamente');
            reconnectAttempts = 0;
            showNotification('Conexión establecida con el servidor', 'success');
            addLogMessage('Conexión establecida con el servidor', 'success');
        };

        wsConnection.onmessage = handleWebSocketMessage;

        wsConnection.onclose = (event) => {
            console.warn('⚠️ WebSocket cerrado. Código:', event.code);
            handleWebSocketClose(event);
        };

        wsConnection.onerror = (error) => {
            console.error('❌ Error en WebSocket:', error);
            addLogMessage('Error en la conexión con el servidor', 'error');
        };

    } catch (error) {
        console.error('❌ Error al crear conexión WebSocket:', error);
        addLogMessage('Error al crear la conexión con el servidor', 'error');
    }
}

// Manejar cierre de WebSocket
function handleWebSocketClose(event) {
    addLogMessage('Conexión perdida con el servidor', 'warning');

    if (reconnectAttempts < WS_CONFIG.maxReconnectAttempts) {
        reconnectAttempts++;
        const delay = WS_CONFIG.reconnectInterval * Math.pow(2, reconnectAttempts - 1);
        console.log(`🔄 Intento de reconexión ${reconnectAttempts} de ${WS_CONFIG.maxReconnectAttempts}`);
        addLogMessage(`Reintentando conexión en ${delay/1000} segundos...`, 'info');
        
        setTimeout(() => {
            if (wsConnection) {
                try {
                    wsConnection.close();
                } catch (e) {
                    console.error('Error cerrando conexión anterior:', e);
                }
            }
            initializeWebSocket();
        }, delay);
    } else {
        console.error('❌ Máximo número de intentos de reconexión alcanzado');
        addLogMessage('No se pudo restablecer la conexión con el servidor', 'error');
    }
}

// Procesar diferentes tipos de mensajes JSON
function processJsonMessage(data) {
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
            console.log('📌 Mensaje recibido sin tipo específico:', data);
    }
}

// Manejar mensajes de log del agente
function handleAgentLogMessage(message) {
    let type = 'info';
    if (message.toLowerCase().includes('error')) {
        type = 'error';
    } else if (message.toLowerCase().includes('warning')) {
        type = 'warning';
    } else if (message.toLowerCase().includes('success') || message.toLowerCase().includes('completed')) {
        type = 'success';
    }

    const cleanMessage = message.replace(/^Agent agt_[^\s]+\s*/, '');
    addLogMessage(cleanMessage, type);
}

// Actualizar estado del agente
function updateAgentStatus(data) {
    try {
        console.group('Actualización Estado Agente');
        console.log('Datos recibidos:', data);

        const agentElement = document.querySelector(`[data-agent-id="${data.agent_id}"]`);
        if (agentElement) {
            const statusElement = agentElement.querySelector('.agent-status');
            if (statusElement) {
                statusElement.className = `agent-status status-${data.status}`;
                statusElement.textContent = data.status;
                console.log('✅ Estado del agente actualizado');
            }
        } else {
            console.warn('⚠️ Elemento del agente no encontrado');
        }
        console.groupEnd();
    } catch (error) {
        console.error('❌ Error al actualizar estado del agente:', error);
        console.groupEnd();
    }
}

// Actualizar estado de la impresora
function updatePrinterStatus(data) {
    try {
        console.group('Actualización Estado Impresora');
        console.log('Datos recibidos:', data);

        const printerElement = document.querySelector(`[data-printer-id="${data.printer_id}"]`);
        if (printerElement) {
            const statusElement = printerElement.querySelector('.printer-status');
            if (statusElement) {
                statusElement.className = `printer-status status-${data.status}`;
                statusElement.textContent = data.status;
                console.log('✅ Estado de la impresora actualizado');
            }
        } else {
            console.warn('⚠️ Elemento de la impresora no encontrado');
        }
        console.groupEnd();
    } catch (error) {
        console.error('❌ Error al actualizar estado de la impresora:', error);
        console.groupEnd();
    }
}

// Manejar mensajes de error
function handleErrorMessage(data) {
    console.error('❌ Error recibido del servidor:', data.error);
    showNotification(data.error.message || 'Error del servidor', 'error');
}

// Función para añadir mensaje de log
function addLogMessage(message, type = 'info') {
    const logContainer = document.getElementById('logMessages');
    if (logContainer) {
        const logEntry = document.createElement('div');
        const timestamp = new Date().toLocaleTimeString();
        
        let classes = 'py-1 px-2 rounded';
        let symbol = '';
        switch (type) {
            case 'success':
                classes += ' text-green-700 bg-green-50';
                symbol = '✓';
                break;
            case 'error':
                classes += ' text-red-700 bg-red-50';
                symbol = '✗';
                break;
            case 'warning':
                classes += ' text-yellow-700 bg-yellow-50';
                symbol = '⚠';
                break;
            default:
                classes += ' text-gray-700';
                symbol = '→';
        }

        logEntry.className = classes;
        logEntry.innerHTML = `<span class="text-xs text-gray-500">${timestamp}</span> ${symbol} ${message}`;
        
        logContainer.appendChild(logEntry);
        logContainer.scrollTop = logContainer.scrollHeight;

        // Mantener solo los últimos N mensajes
        while (logContainer.children.length > 50) {
            logContainer.removeChild(logContainer.firstChild);
        }
    }
}
// PARTE 3: Inicialización de Componentes y Formularios

// Función para inicializar el filtro de búsqueda
function initializeSearchFilter() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
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
        installForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            try {
                const submitButton = installForm.querySelector('button[type="submit"]');
                const driverId = document.getElementById('driver').value;
                const printerIp = document.getElementById('printerIp').value;

                if (!driverId || !printerIp) {
                    showNotification('Por favor complete todos los campos', 'error');
                    addLogMessage('Error: Faltan campos requeridos', 'error');
                    return;
                }

                // Guardar información de la instalación actual
                WS_CONFIG.currentInstallation = {
                    driverId,
                    printerIp,
                    startTime: new Date()
                };

                // Deshabilitar el botón y cambiar texto
                submitButton.disabled = true;
                submitButton.innerHTML = 'Instalando...';
                
                addLogMessage('Iniciando instalación de impresora...', 'info');

                const baseUrl = getSecureBaseUrl();
                const response = await fetch(`${baseUrl}/api/v1/printers/install/${currentAgentToken}`, {
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

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `Error en la instalación: ${response.status}`);
                }

                addLogMessage('Comando enviado. La instalación continúa en segundo plano...', 'info');

                // Actualizar UI post-instalación
                const closeButton = document.querySelector('button[onclick="closeModal(\'installPrinterModal\')"]');
                if (closeButton) {
                    closeButton.textContent = 'Cerrar ventana';
                }

                // Deshabilitar campos del formulario
                document.getElementById('driver').disabled = true;
                document.getElementById('printerIp').disabled = true;

            } catch (error) {
                console.error('Error detallado:', error);
                addLogMessage(`Error: ${error.message}`, 'error');
                
                // Reactivar el botón de envío
                submitButton.disabled = false;
                submitButton.innerHTML = 'Instalar';
                
                // Limpiar instalación actual
                WS_CONFIG.currentInstallation = null;
            }
        });
    }
}

// Función para inicializar el select de drivers
async function initializeDriverSelect() {
    const driverSelect = document.getElementById('driver');
    if (!driverSelect) return;

    try {
        addLogMessage('Cargando lista de drivers...', 'info');
        
        const baseUrl = getSecureBaseUrl();
        const response = await fetch(`${baseUrl}/api/v1/drivers`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error(`Error al obtener drivers. Status: ${response.status}`);
        }

        const drivers = await response.json();
        if (!Array.isArray(drivers)) {
            throw new Error('El formato de datos devuelto no es válido');
        }

        // Limpiar y preparar el select
        driverSelect.innerHTML = '<option value="">Seleccione un driver</option>';
        
        // Ordenar drivers
        const sortedDrivers = drivers.sort((a, b) => {
            return a.manufacturer.localeCompare(b.manufacturer) || 
                   a.model.localeCompare(b.model);
        });

        // Agregar opciones
        sortedDrivers.forEach((driver) => {
            const option = document.createElement('option');
            option.value = driver.id;
            option.textContent = `${driver.manufacturer} - ${driver.model} (${driver.driver_filename})`;
            driverSelect.appendChild(option);
        });

        addLogMessage('Drivers cargados correctamente', 'success');

    } catch (error) {
        console.error('Error completo inicializando drivers:', error);
        addLogMessage(`Error al cargar drivers: ${error.message}`, 'error');
        driverSelect.innerHTML = '<option value="">Error al cargar drivers</option>';
        driverSelect.disabled = true;
    }
}

// Función para mostrar el modal de instalación de impresora
function showInstallPrinter(agentToken) {
    currentAgentToken = agentToken;
    
    const modal = document.getElementById('installPrinterModal');
    if (modal) {
        modal.classList.remove('hidden');
        
        // Resetear formulario
        const form = document.getElementById('installPrinterForm');
        form.reset();
        
        // Habilitar campos
        document.getElementById('driver').disabled = false;
        document.getElementById('printerIp').disabled = false;
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Instalar';
        }
        
        // Limpiar logs
        const logMessages = document.getElementById('logMessages');
        if (logMessages) {
            logMessages.innerHTML = '';
            addLogMessage('Iniciando proceso de instalación...', 'info');
        }
        
        initializeDriverSelect();
    }
}
// PARTE 4: UI, Modales y Notificaciones

// Función para cerrar modal
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        // Verificar instalación en progreso
        if (WS_CONFIG.currentInstallation) {
            const installationTime = (new Date() - WS_CONFIG.currentInstallation.startTime) / 1000;
            if (installationTime < 60) {
                if (!confirm('La instalación está en progreso. ¿Está seguro que desea cerrar la ventana?')) {
                    return;
                }
            }
        }
        
        modal.classList.add('hidden');
        if (modalId === 'installPrinterModal') {
            document.getElementById('installPrinterForm').reset();
            WS_CONFIG.currentInstallation = null;
            const logMessages = document.getElementById('logMessages');
            if (logMessages) {
                logMessages.innerHTML = '';
            }
        }
    }
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    const notificationContainer = document.getElementById('notification-container');
    if (notificationContainer) {
        const notification = document.createElement('div');
        notification.classList.add('notification', `notification-${type}`);
        notification.innerHTML = `
            <strong>${type.toUpperCase()}:</strong> 
            ${message}
            <button class="close-notification">&times;</button>
        `;

        const closeButton = notification.querySelector('.close-notification');
        closeButton.addEventListener('click', () => {
            notification.remove();
        });

        notificationContainer.appendChild(notification);

        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                notification.remove();
            }, 500);
        }, 5000);
    }
}

// Función para mostrar información del agente
async function showAgentInfo(agentId) {
    const modal = document.getElementById("agentInfoModal");
    const content = document.getElementById("agentInfoContent");
    
    if (!modal || !content) return;

    modal.classList.remove("hidden");
    content.innerHTML = `
        <div class="flex justify-center items-center p-8">
            <i class="fas fa-circle-notch fa-spin text-blue-500 text-3xl mr-3"></i>
            <span class="text-gray-600 text-lg">Cargando información...</span>
        </div>
    `;

    try {
        const baseUrl = getSecureBaseUrl();
        const response = await fetch(`${baseUrl}/api/v1/agents/${agentId}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new Error(`Error al cargar los datos: ${response.status}`);
        }

        const agent = await response.json();
        console.log('Datos del agente:', agent);

        // Actualizar el contenido con los datos del agente
        content.innerHTML = generateAgentInfoHTML(agent);

    } catch (error) {
        console.error('Error:', error);
        content.innerHTML = generateErrorHTML(error.message);
    }
}

// Función para eliminar un agente
async function deleteAgent(agentId) {
    if (!confirm("¿Estás seguro de que deseas eliminar este agente?")) {
        return;
    }

    try {
        const baseUrl = getSecureBaseUrl();
        const response = await fetch(`${baseUrl}/api/v1/agents/${agentId}`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
            },
            credentials: 'same-origin'
        });

        if (response.ok) {
            showNotification("Agente eliminado correctamente.", "success");
            location.reload();
        } else {
            const errorData = await response.json();
            showNotification(`Error: ${errorData.detail}`, "error");
        }
    } catch (error) {
        console.error("Error eliminando el agente:", error);
        showNotification("Ocurrió un error al intentar eliminar el agente.", "error");
    }
}

// Función auxiliar para generar HTML de error
function generateErrorHTML(errorMessage) {
    return `
        <div class="text-center py-8">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mb-4">
                <i class="fas fa-exclamation-circle text-red-500 text-2xl"></i>
            </div>
            <h3 class="text-lg font-medium text-gray-900 mb-2">Error al cargar la información</h3>
            <p class="text-sm text-gray-500">${errorMessage}</p>
        </div>
    `;
}

// Función auxiliar para generar HTML de información del agente
function generateAgentInfoHTML(agent) {
    return `
        <div class="grid grid-cols-2 gap-6 p-4">
            <!-- Información Básica -->
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 class="text-lg font-semibold text-gray-900 mb-4">
                    <i class="fas fa-info-circle text-blue-500 mr-2"></i>
                    Información Básica
                </h2>
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span class="text-gray-600">Hostname:</span>
                        <span class="font-medium">${agent.hostname}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600">Status:</span>
                        <span class="font-medium ${
                            agent.status === 'online' ? 'text-green-500' : 'text-red-500'
                        }">${agent.status}</span>
                    </div>
                    <!-- Agregar más información según necesites -->
                </div>
            </div>
            
            <!-- Sistema -->
            <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h2 class="text-lg font-semibold text-gray-900 mb-4">
                    <i class="fas fa-desktop text-green-500 mr-2"></i>
                    Sistema
                </h2>
                <div class="space-y-3">
                    <div class="flex justify-between">
                        <span class="text-gray-600">OS:</span>
                        <span class="font-medium">${agent.system_info.Sistema["Nombre del SO"]}</span>
                    </div>
                    <div class="flex justify-between">
                        <span class="text-gray-600">Versión:</span>
                        <span class="font-medium">${agent.system_info.Sistema["Versión del SO"]}</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Exportar funciones necesarias
export {
    initializeWebSocket,
    showNotification,
    addLogMessage,
    showAgentInfo,
    deleteAgent,
    closeModal
};