// static/js/agents.js

// Variables globales
let currentAgentToken = '';
let agentToDelete = null;

// Configuración WebSocket
const WS_CONFIG = {
    url: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws/status`,
    reconnectInterval: 1000,
    maxReconnectAttempts: 10,
    currentInstallation: null
};

const API_CONFIG = {
    baseUrl: 'https://copierconnectremote.com',  // Forzar HTTPS
    apiVersion: '/api/v1'
};

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function () {
    initializeWebSocket();
    initializeSearchFilter();
    initializeFormHandlers();
    initializeDriverSelect(); // Añadido para cargar drivers al inicio
});
// Función para manejar la reconexión del WebSocket
function handleWebSocketReconnection(event) {
    console.log('WebSocket cerrado. Código:', event.code);
    addLogMessage({
        timestamp: new Date().toISOString().replace('T', ' ').split('.')[0],
        type: 'warning',
        message: 'Conexión interrumpida. Reintentando...'
    });

    // Si hay una instalación en progreso, intentar reconectar
    if (WS_CONFIG.currentInstallation) {
        if (reconnectAttempts < WS_CONFIG.maxReconnectAttempts) {
            reconnectAttempts++;
            console.log(`Intento de reconexión ${reconnectAttempts} de ${WS_CONFIG.maxReconnectAttempts}`);
            setTimeout(initializeWebSocket, WS_CONFIG.reconnectInterval);
        } else {
            addLogMessage({
                timestamp: new Date().toISOString().replace('T', ' ').split('.')[0],
                type: 'warning',
                message: 'No se pudo restablecer la conexión. La instalación continúa en segundo plano.'
            });
        }
    }
}

// Función para añadir un mensaje de log
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
// Inicializar WebSocket
function initializeWebSocket() {
    try {
        console.group('Inicialización WebSocket');
        console.log('Intentando conectar WebSocket a:', WS_CONFIG.url);
        
        wsConnection = new WebSocket(WS_CONFIG.url);

        wsConnection.onopen = () => {
            console.log('✅ WebSocket conectado exitosamente');
            reconnectAttempts = 0;
            showNotification('Conexión establecida con el servidor', 'success');
            addLogMessage('Conexión establecida con el servidor', 'success');
        };

        wsConnection.onmessage = (event) => {
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
        };

        wsConnection.onclose = (event) => {
            console.warn('⚠️ WebSocket cerrado. Código:', event.code);
            handleWebSocketClose(event);
        };

        wsConnection.onerror = (error) => {
            console.error('❌ Error en WebSocket:', error);
            showNotification('Error en la conexión con el servidor', 'error');
            addLogMessage('Error en la conexión con el servidor', 'error');
        };

    } catch (error) {
        console.error('❌ Error al crear conexión WebSocket:', error);
        showNotification('Error al crear la conexión con el servidor', 'error');
        addLogMessage('Error al crear la conexión con el servidor', 'error');
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



// Funciones auxiliares para manejar diferentes tipos de mensajes
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

// Manejar cierre de WebSocket
function handleWebSocketClose(event) {
    showNotification('Conexión perdida con el servidor', 'warning');

    if (reconnectAttempts < WS_CONFIG.maxReconnectAttempts) {
        reconnectAttempts++;
        console.log(`🔄 Intento de reconexión ${reconnectAttempts} de ${WS_CONFIG.maxReconnectAttempts}`);
        setTimeout(initializeWebSocket, WS_CONFIG.reconnectInterval);
    } else {
        console.error('❌ Máximo número de intentos de reconexión alcanzado');
        showNotification('No se pudo restablecer la conexión con el servidor', 'error');
    }
}

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

                // Validación de campos
                if (!driverId || !printerIp) {
                    console.warn('Campos incompletos:', { driverId, printerIp });
                    showNotification('Por favor complete todos los campos', 'error');
                    addLogMessage('Error: Faltan campos requeridos', 'error');
                    return;
                }

                // Log de inicio de instalación
                console.log('Iniciando instalación:', {
                    driverId,
                    printerIp,
                    agentToken: currentAgentToken
                });

                // Guardar información de la instalación actual
                WS_CONFIG.currentInstallation = {
                    driverId,
                    printerIp,
                    startTime: new Date()
                };

                // Deshabilitar el botón de envío y cambiar el texto
                submitButton.disabled = true;
                submitButton.innerHTML = 'Instalando...';
                
                addLogMessage('Iniciando instalación de impresora...', 'info');

                // Construir URL con el protocolo correcto
                const installUrl = `${window.location.protocol}//${window.location.host}/api/v1/printers/install/${currentAgentToken}`;
                console.log('URL de instalación:', installUrl);

                const response = await fetch(installUrl, {
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

                console.log('Comando de instalación enviado correctamente');
                addLogMessage('Comando enviado. La instalación continúa en segundo plano...', 'info');

                // Cambiar el texto del botón de cerrar
                const closeButton = document.querySelector('button[onclick="closeModal(\'installPrinterModal\')"]');
                if (closeButton) {
                    closeButton.textContent = 'Cerrar ventana';
                }

                // Deshabilitar los campos del formulario
                document.getElementById('driver').disabled = true;
                document.getElementById('printerIp').disabled = true;

            } catch (error) {
                console.error('Error detallado en la instalación:', error);
                addLogMessage(`Error: ${error.message}`, 'error');
                
                // Reactivar el botón de envío en caso de error
                const submitButton = installForm.querySelector('button[type="submit"]');
                if (submitButton) {
                    submitButton.disabled = false;
                    submitButton.innerHTML = 'Instalar';
                }
                
                // Limpiar instalación actual
                WS_CONFIG.currentInstallation = null;
            }
        });
    } else {
        console.warn('Formulario de instalación no encontrado en el DOM');
    }
}
// Función para inicializar el select de drivers
async function initializeDriverSelect() {
    const driverSelect = document.getElementById('driver');
    if (!driverSelect) return;

    try {
        addLogMessage('Cargando lista de drivers...', 'info');
        
        // Usar la URL con HTTPS forzado
        const driversUrl = `${API_CONFIG.baseUrl}${API_CONFIG.apiVersion}/drivers`;
        console.log('Intentando cargar drivers desde:', driversUrl);

        const response = await fetch(driversUrl, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Error al obtener drivers. Status: ${response.status}, Respuesta: ${errorText}`);
            throw new Error(`Error al obtener drivers. Status: ${response.status}`);
        }

        const drivers = await response.json();
        console.log('Drivers cargados exitosamente:', drivers);

        if (!Array.isArray(drivers)) {
            console.error('El formato de datos devuelto no es un array:', drivers);
            throw new Error('El formato de datos devuelto no es válido');
        }

        // Limpiar y repoblar el select
        driverSelect.innerHTML = '<option value="">Seleccione un driver</option>';
        
        drivers.forEach((driver) => {
            const option = document.createElement('option');
            option.value = driver.id;
            option.textContent = `${driver.manufacturer} - ${driver.model} (${driver.driver_filename})`;
            driverSelect.appendChild(option);
        });

        addLogMessage('Drivers cargados correctamente', 'success');

    } catch (error) {
        console.error('Error completo inicializando drivers:', error);
        addLogMessage(`Error al cargar drivers: ${error.message}`, 'error');
        showNotification(`Error al cargar drivers: ${error.message}`, 'error');
    }
}
// Función para mostrar el modal de instalación de impresora
function showInstallPrinter(agentToken) {
    currentAgentToken = agentToken;
    
    const modal = document.getElementById('installPrinterModal');
    if (modal) {
        modal.classList.remove('hidden');
        
        // Resetear el formulario y habilitar campos
        const form = document.getElementById('installPrinterForm');
        form.reset();
        
        // Habilitar campos y botones
        document.getElementById('driver').disabled = false;
        document.getElementById('printerIp').disabled = false;
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Instalar';
        }
        
        // Limpiar logs anteriores
        const logMessages = document.getElementById('logMessages');
        if (logMessages) {
            logMessages.innerHTML = '';
            addLogMessage('Iniciando proceso de instalación...', 'info');
        }
        
        initializeDriverSelect();
    }
}


// Función para cerrar un modal por ID
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        // Verificar si hay una instalación en progreso
        if (WS_CONFIG.currentInstallation) {
            const installationTime = (new Date() - WS_CONFIG.currentInstallation.startTime) / 1000;
            if (installationTime < 60) { // Si han pasado menos de 60 segundos
                if (!confirm('La instalación está en progreso. ¿Está seguro que desea cerrar la ventana?')) {
                    return;
                }
            }
        }
        
        modal.classList.add('hidden');
        if (modalId === 'installPrinterModal') {
            document.getElementById('installPrinterForm').reset();
            WS_CONFIG.currentInstallation = null; // Limpiar instalación actual
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


async function showAgentInfo(agentId) {
    const modal = document.getElementById("agentInfoModal");
    const content = document.getElementById("agentInfoContent");

    modal.classList.remove("hidden");
    content.innerHTML = `
        <div class="flex justify-center items-center p-8">
            <i class="fas fa-circle-notch fa-spin text-blue-500 text-3xl mr-3"></i>
            <span class="text-gray-600 text-lg">Cargando información...</span>
        </div>
    `;

    try {
        const response = await fetch(`/api/v1/agents/${agentId}`);
        if (!response.ok) {
            throw new Error(`Error al cargar los datos: ${response.status}`);
        }
        const agent = await response.json();
        console.log('Datos del agente:', agent);

        content.innerHTML = `
            <div class="grid grid-cols-2 gap-6 p-4">
                <!-- Información Básica del Agente -->
                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h2 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <i class="fas fa-desktop text-blue-500 mr-2"></i>
                        Información del Agente
                    </h2>
                    <div class="space-y-4">
                        <div class="flex items-center">
                            <div class="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                                <i class="fas fa-laptop text-blue-500"></i>
                            </div>
                            <div class="ml-3 flex-1">
                                <span class="text-sm text-gray-500">Hostname</span>
                                <p class="font-medium">${agent.hostname}</p>
                            </div>
                        </div>
                        <div class="flex items-center">
                            <div class="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
                                <i class="fas fa-user text-green-500"></i>
                            </div>
                            <div class="ml-3 flex-1">
                                <span class="text-sm text-gray-500">Usuario</span>
                                <p class="font-medium">${agent.username}</p>
                            </div>
                        </div>
                        <div class="flex items-center">
                            <div class="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
                                <i class="fas fa-network-wired text-purple-500"></i>
                            </div>
                            <div class="ml-3 flex-1">
                                <span class="text-sm text-gray-500">IP</span>
                                <p class="font-medium">${agent.ip_address}</p>
                            </div>
                        </div>
                        <div class="flex items-center">
                            <div class="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center">
                                <i class="fas fa-cog text-indigo-500"></i>
                            </div>
                            <div class="ml-3 flex-1">
                                <span class="text-sm text-gray-500">Tipo de Dispositivo</span>
                                <p class="font-medium">${agent.device_type}</p>
                            </div>
                        </div>
                        <div class="flex items-center">
                            <div class="w-10 h-10 rounded-lg bg-${agent.status === 'online' ? 'green' : 'red'}-50 flex items-center justify-center">
                                <i class="fas fa-circle text-${agent.status === 'online' ? 'green' : 'red'}-500"></i>
                            </div>
                            <div class="ml-3 flex-1">
                                <span class="text-sm text-gray-500">Estado</span>
                                <p class="font-medium capitalize">${agent.status}</p>
                            </div>
                        </div>
                        <div class="flex items-center">
                            <div class="w-10 h-10 rounded-lg bg-yellow-50 flex items-center justify-center">
                                <i class="fas fa-key text-yellow-500"></i>
                            </div>
                            <div class="ml-3 flex-1">
                                <span class="text-sm text-gray-500">Token</span>
                                <p class="font-mono text-sm">${agent.token}</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Información del Sistema -->
                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h2 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <i class="fas fa-microchip text-indigo-500 mr-2"></i>
                        Sistema Operativo
                    </h2>
                    <div class="space-y-4">
                        <div class="flex items-center">
                            <div class="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center">
                                <i class="fas fa-windows text-indigo-500"></i>
                            </div>
                            <div class="ml-3 flex-1">
                                <span class="text-sm text-gray-500">Sistema Operativo</span>
                                <p class="font-medium">${agent.system_info.Sistema["Nombre del SO"]}</p>
                                <p class="text-sm text-gray-500">Versión ${agent.system_info.Sistema["Versión del SO"]}</p>
                            </div>
                        </div>
                        <div class="flex items-center">
                            <div class="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                                <i class="fas fa-microchip text-blue-500"></i>
                            </div>
                            <div class="ml-3 flex-1">
                                <span class="text-sm text-gray-500">Arquitectura</span>
                                <p class="font-medium">${agent.system_info.Sistema.Arquitectura}</p>
                            </div>
                        </div>
                        <div class="flex items-center">
                            <div class="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
                                <i class="fas fa-laptop text-green-500"></i>
                            </div>
                            <div class="ml-3 flex-1">
                                <span class="text-sm text-gray-500">Nombre del dispositivo</span>
                                <p class="font-medium">${agent.system_info.Sistema["Nombre del dispositivo"]}</p>
                            </div>
                        </div>
                        <div class="flex items-center">
                            <div class="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center">
                                <i class="fas fa-user text-red-500"></i>
                            </div>
                            <div class="ml-3 flex-1">
                                <span class="text-sm text-gray-500">Nombre del usuario</span>
                                <p class="font-medium">${agent.system_info.Sistema["Nombre del usuario"]}</p>
                            </div>
                        </div>
                        <div class="flex items-center">
                            <div class="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
                                <i class="fas fa-microchip text-purple-500"></i>
                            </div>
                            <div class="ml-3 flex-1">
                                <span class="text-sm text-gray-500">Procesador</span>
                                <p class="font-medium">${agent.system_info.Sistema.Procesador}</p>
                            </div>
                        </div>
                    </div>
                </div>
                <!-- Información de Hardware -->
                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h2 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <i class="fas fa-memory text-red-500 mr-2"></i>
                        Hardware
                    </h2>
                    <div class="space-y-4">
                        <!-- CPU -->
                        <div class="border-b pb-4">
                            <div class="flex items-center">
                                <div class="w-10 h-10 rounded-lg bg-red-50 flex items-center justify-center">
                                    <i class="fas fa-microchip text-red-500"></i>
                                </div>
                                <div class="ml-3 flex-1">
                                    <span class="text-sm text-gray-500">Procesador</span>
                                    <p class="font-medium">${agent.system_info.CPU.Modelo}</p>
                                    <div class="grid grid-cols-2 gap-2 mt-1">
                                        <p class="text-sm text-gray-500">
                                            Núcleos físicos: ${agent.system_info.CPU["Núcleos físicos"]}
                                        </p>
                                        <p class="text-sm text-gray-500">
                                            Núcleos lógicos: ${agent.system_info.CPU["Núcleos lógicos"]}
                                        </p>
                                        <p class="text-sm text-gray-500">
                                            Frecuencia: ${agent.system_info.CPU["Frecuencia (MHz)"]} MHz
                                        </p>
                                        <p class="text-sm text-gray-500">
                                            Uso actual: ${agent.system_info.CPU["Uso actual (%)"]}%
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- RAM -->
                        <div class="border-b pb-4">
                            <div class="flex items-center">
                                <div class="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                                    <i class="fas fa-memory text-blue-500"></i>
                                </div>
                                <div class="ml-3 flex-1">
                                    <span class="text-sm text-gray-500">Memoria RAM</span>
                                    <p class="font-medium">${agent.system_info.Memoria["Total RAM (GB)"]} GB Total</p>
                                    <div class="grid grid-cols-2 gap-2 mt-1">
                                        <p class="text-sm text-gray-500">
                                            Disponible: ${agent.system_info.Memoria["Disponible RAM (GB)"]} GB
                                        </p>
                                        <p class="text-sm text-gray-500">
                                            Uso: ${agent.system_info.Memoria["Uso de RAM (%)"]}%
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Batería -->
                        <div class="border-b pb-4">
                            <div class="flex items-center">
                                <div class="w-10 h-10 rounded-lg bg-yellow-50 flex items-center justify-center">
                                    <i class="fas fa-battery-full text-yellow-500"></i>
                                </div>
                                <div class="ml-3 flex-1">
                                    <span class="text-sm text-gray-500">Batería</span>
                                    <p class="font-medium">${agent.system_info.Batería.Porcentaje}% ${agent.system_info.Batería.Enchufado ? '(Conectado)' : '(Desconectado)'}</p>
                                </div>
                            </div>
                        </div>

                        <!-- GPU -->
                        <div class="">
                            <div class="flex items-center">
                                <div class="w-10 h-10 rounded-lg bg-green-50 flex items-center justify-center">
                                    <i class="fas fa-desktop text-green-500"></i>
                                </div>
                                <div class="ml-3 flex-1">
                                    <span class="text-sm text-gray-500">Tarjeta Gráfica</span>
                                    <p class="font-medium">${agent.system_info["Tarjetas Gráficas"]}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Información de Almacenamiento -->
                <div class="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h2 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <i class="fas fa-hdd text-purple-500 mr-2"></i>
                        Almacenamiento
                    </h2>
                    <div class="space-y-4">
                        <!-- Resumen de Espacio -->
                        <div class="border-b pb-4">
                            <div class="flex items-center">
                                <div class="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
                                    <i class="fas fa-chart-pie text-purple-500"></i>
                                </div>
                                <div class="ml-3 flex-1">
                                    <span class="text-sm text-gray-500">Espacio Total</span>
                                    <p class="font-medium">${agent.system_info["Espacio en Disco"]["Total (GB)"]} GB</p>
                                    <div class="grid grid-cols-2 gap-2 mt-1">
                                        <p class="text-sm text-gray-500">
                                            Usado: ${agent.system_info["Espacio en Disco"]["Usado (GB)"]} GB
                                        </p>
                                        <p class="text-sm text-gray-500">
                                            Libre: ${agent.system_info["Espacio en Disco"]["Libre (GB)"]} GB
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Detalles de Discos -->
                        ${agent.system_info.Discos.map((disco, index) => `
                            <div class="border-b last:border-0 pb-4 last:pb-0">
                                <div class="flex items-center">
                                    <div class="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
                                        <i class="fas fa-hdd text-purple-500"></i>
                                    </div>
                                    <div class="ml-3 flex-1">
                                        <span class="text-sm text-gray-500">Disco ${disco.Dispositivo}</span>
                                        <p class="font-medium">${disco["Total (GB)"]} GB (${disco["Tipo de sistema de archivos"]})</p>
                                        <div class="grid grid-cols-2 gap-2 mt-1">
                                            <p class="text-sm text-gray-500">
                                                Punto de montaje: ${disco["Punto de montaje"]}
                                            </p>
                                            <p class="text-sm text-gray-500">
                                                Usado: ${disco["Usado (GB)"]} GB
                                            </p>
                                            <p class="text-sm text-gray-500">
                                                Disponible: ${disco["Disponible (GB)"]} GB
                                            </p>
                                            <p class="text-sm text-gray-500">
                                                Uso: ${disco["Porcentaje de uso (%)"]}%
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Información de Red -->
                <div class="col-span-2 bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                    <h2 class="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <i class="fas fa-network-wired text-blue-500 mr-2"></i>
                        Interfaces de Red
                    </h2>
                    <div class="grid grid-cols-2 gap-4">
                        ${Object.entries(agent.system_info.Red).map(([interfaceName, configs]) => `
                            <div class="bg-gray-50 rounded-lg p-4">
                                <div class="flex items-center mb-3">
                                    <div class="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                                        <i class="fas fa-${
                                            interfaceName.toLowerCase().includes('wi-fi') ? 'wifi' : 
                                            interfaceName.toLowerCase().includes('ethernet') ? 'ethernet' : 
                                            interfaceName.toLowerCase().includes('bluetooth') ? 'bluetooth' : 
                                            'network-wired'
                                        } text-blue-500"></i>
                                    </div>
                                    <div class="ml-3">
                                        <span class="font-medium text-gray-900">${interfaceName}</span>
                                    </div>
                                </div>
                                <div class="space-y-2">
                                    ${configs.map(config => `
                                        <div class="bg-white rounded p-2">
                                            <div class="flex justify-between items-center">
                                                <span class="text-sm text-gray-500">${config.Tipo}:</span>
                                                <span class="text-sm font-medium">${config.Dirección}</span>
                                            </div>
                                            ${config["Máscara de red"] ? `
                                                <div class="flex justify-between items-center mt-1">
                                                    <span class="text-sm text-gray-500">Máscara:</span>
                                                    <span class="text-sm font-medium">${config["Máscara de red"]}</span>
                                                </div>
                                            ` : ''}
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;

    } catch (error) {
        console.error('Error:', error);
        content.innerHTML = `
            <div class="text-center py-8">
                <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mb-4">
                    <i class="fas fa-exclamation-circle text-red-500 text-2xl"></i>
                </div>
                <h3 class="text-lg font-medium text-gray-900 mb-2">Error al cargar la información</h3>
                <p class="text-sm text-gray-500">${error.message}</p>
            </div>
        `;
    }
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add("hidden");
}


async function deleteAgent(agentId) {
    if (!confirm("¿Estás seguro de que deseas eliminar este agente?")) {
        return;
    }

    try {
        const response = await fetch(`/api/v1/agents/${agentId}`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
            },
        });

        if (response.ok) {
            alert("Agente eliminado correctamente.");
            location.reload(); // Recargar la página para actualizar la lista
        } else {
            const errorData = await response.json();
            alert(`Error: ${errorData.detail}`);
        }
    } catch (error) {
        console.error("Error eliminando el agente:", error);
        alert("Ocurrió un error al intentar eliminar el agente.");
    }
}
