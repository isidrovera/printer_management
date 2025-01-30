// static/js/agents.js

// Variables globales
let currentAgentToken = '';
let agentToDelete = null;

// Configuración WebSocket
const WS_CONFIG = {
    url: `ws://${window.location.host}/api/v1/ws/status`,
    reconnectInterval: 1000,
    maxReconnectAttempts: 10,  // Aumentamos el número de reintentos
    currentInstallation: null  // Para trackear instalación en progreso
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

                if (!driverId || !printerIp) {
                    showNotification('Por favor complete todos los campos', 'error');
                    addLogMessage({
                        timestamp: new Date().toISOString().replace('T', ' ').split('.')[0],
                        type: 'error',
                        message: 'Error: Faltan campos requeridos'
                    });
                    return;
                }

                // Guardar información de la instalación actual
                WS_CONFIG.currentInstallation = {
                    driverId,
                    printerIp,
                    startTime: new Date()
                };

                // Deshabilitar el botón de envío y cambiar el texto
                submitButton.disabled = true;
                submitButton.innerHTML = 'Instalando...';
                
                addLogMessage({
                    timestamp: new Date().toISOString().replace('T', ' ').split('.')[0],
                    type: 'info',
                    message: 'Iniciando instalación de impresora...'
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

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `Error en la instalación: ${response.status}`);
                }

                addLogMessage({
                    timestamp: new Date().toISOString().replace('T', ' ').split('.')[0],
                    type: 'info',
                    message: 'Comando enviado. La instalación continúa en segundo plano...'
                });

                // Cambiar el texto del botón de cerrar
                const closeButton = document.querySelector('button[onclick="closeModal(\'installPrinterModal\')"]');
                if (closeButton) {
                    closeButton.textContent = 'Cerrar ventana';
                }

                // Deshabilitar los campos del formulario
                document.getElementById('driver').disabled = true;
                document.getElementById('printerIp').disabled = true;

            } catch (error) {
                console.error('Error detallado:', error);
                addLogMessage({
                    timestamp: new Date().toISOString().replace('T', ' ').split('.')[0],
                    type: 'error',
                    message: `Error: ${error.message}`
                });
                
                // Reactivar el botón de envío en caso de error
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
        
        const response = await fetch('/api/v1/drivers', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const text = await response.text();
            throw new Error(`Error al obtener drivers. Status: ${response.status}`);
        }

        const drivers = await response.json();
        
        if (!Array.isArray(drivers)) {
            throw new Error('El formato de datos devuelto no es válido');
        }

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

    // 🏷️ Mostrar mensaje de carga
    content.innerHTML = `<p class="text-center text-gray-500">Cargando información...</p>`;

    try {
        // 🔄 Obtener los datos del agente desde el servidor
        const response = await fetch(`/api/v1/agents/${agentId}`);
        if (!response.ok) {
            throw new Error(`Error en la solicitud: ${response.status}`);
        }
        const agent = await response.json();

        // 🔍 Verificaciones para evitar errores de propiedades undefined
        const cpuInfo = agent.cpu_info || {};
        const memoryInfo = agent.memory_info || {};
        const diskInfo = agent.disk_info || [];
        const networkInfo = agent.network_info || {};
        const gpuInfo = agent.gpu_info || { Nombre: "No disponible" };
        const batteryInfo = agent.battery_info || { Porcentaje: "No disponible", Enchufado: false };
        const diskUsage = agent.disk_usage || {};

        // 🖼️ Generar la vista con los datos del agente
        content.innerHTML = `
            <div class="grid grid-cols-2 gap-4">
                <div class="col-span-2">
                    <h4 class="text-lg font-bold flex items-center text-blue-600">
                        <i data-lucide="server" class="h-6 w-6 mr-2"></i> Información del Servidor
                    </h4>
                </div>
                <div>
                    <p class="text-gray-600"><strong>🖥️ Hostname:</strong> ${agent.hostname || "N/A"}</p>
                    <p class="text-gray-600"><strong>📡 IP:</strong> ${agent.ip_address || "N/A"}</p>
                    <p class="text-gray-600"><strong>💻 Tipo de Dispositivo:</strong> ${agent.device_type || "N/A"}</p>
                    <p class="text-gray-600"><strong>🔌 Estado:</strong> ${agent.status || "N/A"}</p>
                </div>
                <div>
                    <p class="text-gray-600"><strong>👤 Usuario:</strong> ${agent.username || "N/A"}</p>
                    <p class="text-gray-600"><strong>🆔 Token:</strong> ${agent.token || "N/A"}</p>
                </div>

                <!-- CPU -->
                <div class="col-span-2 border-t pt-2">
                    <h4 class="text-md font-semibold flex items-center text-red-500">
                        <i data-lucide="cpu" class="h-5 w-5 mr-2"></i> Procesador
                    </h4>
                    <p class="text-gray-600"><strong>⚙ Modelo:</strong> ${cpuInfo.Modelo || "N/A"}</p>
                    <p class="text-gray-600"><strong>🔄 Frecuencia:</strong> ${cpuInfo["Frecuencia (MHz)"] || "N/A"} MHz</p>
                    <p class="text-gray-600"><strong>📊 Uso:</strong> ${cpuInfo["Uso actual (%)"] || "N/A"}%</p>
                </div>

                <!-- Memoria RAM -->
                <div class="col-span-2 border-t pt-2">
                    <h4 class="text-md font-semibold flex items-center text-purple-500">
                        <i data-lucide="database" class="h-5 w-5 mr-2"></i> Memoria RAM
                    </h4>
                    <p class="text-gray-600"><strong>💾 Total:</strong> ${memoryInfo["Total RAM (GB)"] || "N/A"} GB</p>
                    <p class="text-gray-600"><strong>📉 Disponible:</strong> ${memoryInfo["Disponible RAM (GB)"] || "N/A"} GB</p>
                    <p class="text-gray-600"><strong>📊 Uso:</strong> ${memoryInfo["Uso de RAM (%)"] || "N/A"}%</p>
                </div>

                <!-- Discos -->
                <div class="col-span-2 border-t pt-2">
                    <h4 class="text-md font-semibold flex items-center text-orange-500">
                        <i data-lucide="hard-drive" class="h-5 w-5 mr-2"></i> Discos
                    </h4>
                    ${diskInfo.length > 0 ? diskInfo.map(disk => `
                        <p class="text-gray-600"><strong>🖴 ${disk.Dispositivo || "N/A"}:</strong> 
                        ${disk["Total (GB)"] || "N/A"} GB, Usado: ${disk["Usado (GB)"] || "N/A"} GB</p>
                    `).join("") : `<p class="text-gray-500">🔹 No se encontraron discos.</p>`}
                </div>

                <!-- Red -->
                <div class="col-span-2 border-t pt-2">
                    <h4 class="text-md font-semibold flex items-center text-blue-500">
                        <i data-lucide="wifi" class="h-5 w-5 mr-2"></i> Conexión de Red
                    </h4>
                    ${Object.keys(networkInfo).length > 0 ? 
                        Object.entries(networkInfo).map(([interface, addresses]) => `
                            <p class="text-gray-600"><strong>🌐 ${interface}:</strong></p>
                            ${addresses.map(addr => `<p class="text-gray-600 pl-4">🔹 ${addr.Tipo || "N/A"}: ${addr.Dirección || "N/A"}</p>`).join("")}
                        `).join("") : `<p class="text-gray-500">🔹 No se encontraron conexiones de red.</p>`}
                </div>

                <!-- GPU -->
                <div class="col-span-2 border-t pt-2">
                    <h4 class="text-md font-semibold flex items-center text-green-500">
                        <i data-lucide="monitor" class="h-5 w-5 mr-2"></i> Tarjeta Gráfica
                    </h4>
                    <p class="text-gray-600"><strong>🖥️ GPU:</strong> ${gpuInfo.Nombre || "N/A"}</p>
                </div>

                <!-- Batería -->
                <div class="col-span-2 border-t pt-2">
                    <h4 class="text-md font-semibold flex items-center text-yellow-500">
                        <i data-lucide="battery-charging" class="h-5 w-5 mr-2"></i> Estado de la Batería
                    </h4>
                    <p class="text-gray-600"><strong>🔋 Carga:</strong> ${batteryInfo.Porcentaje || "N/A"}%</p>
                    <p class="text-gray-600"><strong>🔌 Enchufado:</strong> ${batteryInfo.Enchufado ? "Sí" : "No"}</p>
                </div>

                <!-- Espacio en Disco -->
                <div class="col-span-2 border-t pt-2">
                    <h4 class="text-md font-semibold flex items-center text-gray-600">
                        <i data-lucide="database" class="h-5 w-5 mr-2"></i> Espacio en Disco
                    </h4>
                    <p class="text-gray-600"><strong>📁 Total:</strong> ${diskUsage["Total (GB)"] || "N/A"} GB</p>
                    <p class="text-gray-600"><strong>📂 Usado:</strong> ${diskUsage["Usado (GB)"] || "N/A"} GB</p>
                    <p class="text-gray-600"><strong>📦 Libre:</strong> ${diskUsage["Libre (GB)"] || "N/A"} GB</p>
                </div>
            </div>
        `;

    } catch (error) {
        console.error("❌ Error obteniendo los datos del agente:", error);
        content.innerHTML = `<p class="text-red-500">⚠ Error al cargar la información del agente.</p>`;
    }

    // 🔥 Mostrar el modal
    modal.classList.remove("hidden");
}
