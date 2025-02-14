// static/js/agents.js

// agents.js - Parte 1: Configuración principal y WebSocket

// Variables globales con logging
let currentAgentToken = '';
let agentToDelete = null;
let wsConnection = null;
let reconnectAttempts = 0;

// Configuración con logging detallado
const WS_CONFIG = {
    url: `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/ws/status`,
    reconnectInterval: 1000,
    maxReconnectAttempts: 10,
    currentInstallation: null
};

// Logger mejorado
const Logger = {
    group: (name) => {
        console.group(`🔍 ${name}`);
    },
    groupEnd: () => console.groupEnd(),
    info: (msg, data) => {
        console.log(`ℹ️ ${msg}`, data || '');
    },
    success: (msg, data) => {
        console.log(`✅ ${msg}`, data || '');
    },
    warning: (msg, data) => {
        console.warn(`⚠️ ${msg}`, data || '');
    },
    error: (msg, error) => {
        console.error(`❌ ${msg}`, error || '');
    }
};

// Función para obtener la URL base segura
function getSecureBaseUrl() {
    const baseUrl = `${window.location.protocol}//${window.location.host}`;
    Logger.info('Base URL generada:', baseUrl);
    return baseUrl;
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function () {
    Logger.group('Inicialización de la Aplicación');
    try {
        Logger.info('Iniciando componentes principales');
        initializeWebSocket();
        initializeSearchFilter();
        initializeFormHandlers();
        initializeDriverSelect();
        Logger.success('Componentes principales inicializados correctamente');
    } catch (error) {
        Logger.error('Error en la inicialización principal:', error);
    }
    Logger.groupEnd();
});

// Inicialización WebSocket con logging detallado
function initializeWebSocket() {
    Logger.group('Inicialización WebSocket');
    
    try {
        Logger.info('Intentando conectar WebSocket a:', WS_CONFIG.url);
        wsConnection = new WebSocket(WS_CONFIG.url);

        wsConnection.onopen = () => {
            Logger.success('WebSocket conectado exitosamente');
            reconnectAttempts = 0;
            showNotification('Conexión establecida con el servidor', 'success');
            addLogMessage('Conexión establecida con el servidor', 'success');
        };

        wsConnection.onmessage = handleWebSocketMessage;
        wsConnection.onclose = handleWebSocketClose;
        wsConnection.onerror = handleWebSocketError;

    } catch (error) {
        Logger.error('Error al crear conexión WebSocket:', error);
        showNotification('Error al crear la conexión con el servidor', 'error');
        addLogMessage('Error al crear la conexión con el servidor', 'error');
    }

    Logger.groupEnd();
}

// Manejador de mensajes WebSocket
function handleWebSocketMessage(event) {
    Logger.group('Mensaje WebSocket Recibido');
    
    try {
        Logger.info('Mensaje raw recibido:', event.data);

        if (typeof event.data === 'string' && event.data.startsWith('Agent')) {
            Logger.info('Procesando mensaje de log del agente');
            handleAgentLogMessage(event.data);
            return;
        }

        // Intentar parsear como JSON
        let data = JSON.parse(event.data);
        Logger.success('JSON parseado correctamente:', data);
        
        if (data && data.type) {
            processJsonMessage(data);
        } else {
            Logger.warning('Mensaje JSON sin tipo específico:', data);
        }

    } catch (error) {
        Logger.error('Error procesando mensaje WebSocket:', error);
        addLogMessage('Error al procesar mensaje: ' + error.message, 'error');
    }

    Logger.groupEnd();
}

// Manejador de cierre de WebSocket
function handleWebSocketClose(event) {
    Logger.group('Cierre de WebSocket');
    Logger.warning('WebSocket cerrado. Código:', event.code);
    
    showNotification('Conexión perdida con el servidor', 'warning');
    addLogMessage('Conexión interrumpida. Reintentando...', 'warning');

    if (reconnectAttempts < WS_CONFIG.maxReconnectAttempts) {
        reconnectAttempts++;
        Logger.info(`Intento de reconexión ${reconnectAttempts} de ${WS_CONFIG.maxReconnectAttempts}`);
        setTimeout(initializeWebSocket, WS_CONFIG.reconnectInterval);
    } else {
        Logger.error('Máximo número de intentos de reconexión alcanzado');
        showNotification('No se pudo restablecer la conexión con el servidor', 'error');
    }

    Logger.groupEnd();
}

// Manejador de errores WebSocket
function handleWebSocketError(error) {
    Logger.group('Error WebSocket');
    Logger.error('Error en la conexión WebSocket:', error);
    showNotification('Error en la conexión con el servidor', 'error');
    addLogMessage('Error en la conexión con el servidor', 'error');
    Logger.groupEnd();
}

// Procesar diferentes tipos de mensajes JSON
function processJsonMessage(data) {
    Logger.group('Procesamiento de Mensaje JSON');
    Logger.info('Tipo de mensaje:', data.type);

    try {
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
                Logger.warning('Tipo de mensaje no reconocido:', data.type);
        }
    } catch (error) {
        Logger.error('Error procesando mensaje JSON:', error);
    }

    Logger.groupEnd();
}
// agents.js - Parte 2: UI y Actualizaciones de Estado

// Función para añadir mensaje de log con timestamp
function addLogMessage(message, type = 'info') {
    Logger.group('Agregar Mensaje de Log');
    
    try {
        const logContainer = document.getElementById('logMessages');
        if (!logContainer) {
            Logger.warning('Contenedor de logs no encontrado');
            return;
        }

        const logEntry = document.createElement('div');
        const timestamp = new Date().toLocaleTimeString();
        
        // Configurar clases y símbolos según el tipo
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

        // Mantener solo los últimos 50 mensajes
        while (logContainer.children.length > 50) {
            logContainer.removeChild(logContainer.firstChild);
        }

        Logger.success('Mensaje de log agregado correctamente');
    } catch (error) {
        Logger.error('Error al agregar mensaje de log:', error);
    }

    Logger.groupEnd();
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    Logger.group('Mostrar Notificación');
    
    try {
        const notificationContainer = document.getElementById('notification-container');
        if (!notificationContainer) {
            Logger.warning('Contenedor de notificaciones no encontrado');
            return;
        }

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
            Logger.info('Notificación cerrada por el usuario');
        });

        notificationContainer.appendChild(notification);

        // Auto-eliminar después de 5 segundos
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => {
                notification.remove();
                Logger.info('Notificación eliminada automáticamente');
            }, 500);
        }, 5000);

        Logger.success('Notificación mostrada correctamente');
    } catch (error) {
        Logger.error('Error al mostrar notificación:', error);
    }

    Logger.groupEnd();
}

// Función para actualizar estado del agente
function updateAgentStatus(data) {
    Logger.group('Actualización Estado Agente');
    Logger.info('Datos de actualización:', data);

    try {
        const agentElement = document.querySelector(`[data-agent-id="${data.agent_id}"]`);
        if (!agentElement) {
            Logger.warning('Elemento del agente no encontrado:', data.agent_id);
            return;
        }

        const statusElement = agentElement.querySelector('.agent-status');
        if (!statusElement) {
            Logger.warning('Elemento de estado no encontrado');
            return;
        }

        statusElement.className = `agent-status status-${data.status}`;
        statusElement.textContent = data.status;
        Logger.success('Estado del agente actualizado correctamente');

    } catch (error) {
        Logger.error('Error al actualizar estado del agente:', error);
    }

    Logger.groupEnd();
}

// Función para actualizar estado de la impresora
function updatePrinterStatus(data) {
    Logger.group('Actualización Estado Impresora');
    Logger.info('Datos de actualización:', data);

    try {
        const printerElement = document.querySelector(`[data-printer-id="${data.printer_id}"]`);
        if (!printerElement) {
            Logger.warning('Elemento de la impresora no encontrado:', data.printer_id);
            return;
        }

        const statusElement = printerElement.querySelector('.printer-status');
        if (!statusElement) {
            Logger.warning('Elemento de estado no encontrado');
            return;
        }

        statusElement.className = `printer-status status-${data.status}`;
        statusElement.textContent = data.status;
        Logger.success('Estado de la impresora actualizado correctamente');

    } catch (error) {
        Logger.error('Error al actualizar estado de la impresora:', error);
    }

    Logger.groupEnd();
}

// Función para manejar mensajes de error
function handleErrorMessage(data) {
    Logger.group('Manejo de Mensaje de Error');
    Logger.error('Error recibido del servidor:', data.error);
    
    showNotification(data.error.message || 'Error del servidor', 'error');
    addLogMessage(data.error.message || 'Error del servidor', 'error');
    
    Logger.groupEnd();
}

// Función para inicializar el filtro de búsqueda
function initializeSearchFilter() {
    Logger.group('Inicialización Filtro de Búsqueda');

    try {
        const searchInput = document.getElementById('searchInput');
        if (!searchInput) {
            Logger.warning('Elemento de búsqueda no encontrado');
            return;
        }

        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');

            Logger.info('Término de búsqueda:', searchTerm);
            Logger.info('Número de filas a filtrar:', rows.length);

            rows.forEach((row) => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });

            Logger.success('Filtro aplicado correctamente');
        });

        Logger.success('Filtro de búsqueda inicializado');
    } catch (error) {
        Logger.error('Error al inicializar filtro de búsqueda:', error);
    }

    Logger.groupEnd();
}
// agents.js - Parte 3: Manejadores de Formularios e Interacciones API

// Función para inicializar manejadores de formularios
function initializeFormHandlers() {
    Logger.group('Inicialización Manejadores de Formularios');

    try {
        const installForm = document.getElementById('installPrinterForm');
        if (!installForm) {
            Logger.warning('Formulario de instalación no encontrado');
            return;
        }

        installForm.addEventListener('submit', handleInstallFormSubmit);
        Logger.success('Manejadores de formulario inicializados');
    } catch (error) {
        Logger.error('Error al inicializar manejadores de formulario:', error);
    }

    Logger.groupEnd();
}

// Manejador del envío del formulario de instalación
async function handleInstallFormSubmit(e) {
    e.preventDefault();
    Logger.group('Procesando Envío de Formulario de Instalación');

    try {
        const submitButton = e.target.querySelector('button[type="submit"]');
        const driverId = document.getElementById('driver').value;
        const printerIp = document.getElementById('printerIp').value;

        // Validación de campos
        if (!driverId || !printerIp) {
            Logger.warning('Campos incompletos en el formulario');
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

        Logger.info('Iniciando instalación con datos:', WS_CONFIG.currentInstallation);

        // Deshabilitar interfaz durante la instalación
        disableInstallationInterface(submitButton);
        addLogMessage('Iniciando instalación de impresora...', 'info');

        const response = await fetch(`${getSecureBaseUrl()}/api/v1/printers/install/${currentAgentToken}`, {
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

        Logger.success('Comando de instalación enviado correctamente');
        addLogMessage('Comando enviado. La instalación continúa en segundo plano...', 'info');
        updateInstallationInterface();

    } catch (error) {
        Logger.error('Error en la instalación:', error);
        handleInstallationError(error);
    }

    Logger.groupEnd();
}

// Función para inicializar el select de drivers
async function initializeDriverSelect() {
    Logger.group('Inicialización Select de Drivers');

    const driverSelect = document.getElementById('driver');
    if (!driverSelect) {
        Logger.warning('Elemento select de drivers no encontrado');
        return;
    }

    try {
        addLogMessage('Cargando lista de drivers...', 'info');
        
        const response = await fetch(`${getSecureBaseUrl()}/api/v1/drivers`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Error al obtener drivers. Status: ${response.status}`);
        }

        const drivers = await response.json();
        
        if (!Array.isArray(drivers)) {
            throw new Error('El formato de datos devuelto no es válido');
        }

        Logger.info('Drivers obtenidos:', drivers);
        populateDriverSelect(driverSelect, drivers);
        addLogMessage('Drivers cargados correctamente', 'success');

    } catch (error) {
        Logger.error('Error inicializando drivers:', error);
        handleDriverLoadError(error);
    }

    Logger.groupEnd();
}

// Función para poblar el select de drivers
function populateDriverSelect(select, drivers) {
    Logger.group('Poblando Select de Drivers');

    try {
        select.innerHTML = '<option value="">Seleccione un driver</option>';
        drivers.forEach((driver) => {
            const option = document.createElement('option');
            option.value = driver.id;
            option.textContent = `${driver.manufacturer} - ${driver.model} (${driver.driver_filename})`;
            select.appendChild(option);
        });
        Logger.success('Select de drivers poblado correctamente');
    } catch (error) {
        Logger.error('Error al poblar select de drivers:', error);
        throw error;
    }

    Logger.groupEnd();
}

// Función para mostrar el modal de instalación de impresora
function showInstallPrinter(agentToken) {
    Logger.group('Mostrando Modal de Instalación');

    try {
        currentAgentToken = agentToken;
        
        const modal = document.getElementById('installPrinterModal');
        if (!modal) {
            Logger.warning('Modal de instalación no encontrado');
            return;
        }

        modal.classList.remove('hidden');
        resetInstallationForm();
        initializeDriverSelect();
        
        Logger.success('Modal de instalación mostrado correctamente');
    } catch (error) {
        Logger.error('Error al mostrar modal de instalación:', error);
        showNotification('Error al abrir el formulario de instalación', 'error');
    }

    Logger.groupEnd();
}

// Función para mostrar información del agente
async function showAgentInfo(agentId) {
    Logger.group('Mostrando Información del Agente');

    try {
        const modal = document.getElementById("agentInfoModal");
        const content = document.getElementById("agentInfoContent");

        if (!modal || !content) {
            Logger.warning('Elementos del modal de información no encontrados');
            return;
        }

        modal.classList.remove("hidden");
        showLoadingState(content);

        const response = await fetch(`${getSecureBaseUrl()}/api/v1/agents/${agentId}`);
        if (!response.ok) {
            throw new Error(`Error al cargar los datos: ${response.status}`);
        }

        const agent = await response.json();
        Logger.info('Datos del agente recibidos:', agent);
        updateAgentInfoContent(content, agent);
        
        Logger.success('Información del agente mostrada correctamente');
    } catch (error) {
        Logger.error('Error al mostrar información del agente:', error);
        handleAgentInfoError(content, error);
    }

    Logger.groupEnd();
}

// Función para eliminar un agente
async function deleteAgent(agentId) {
    Logger.group('Eliminando Agente');

    if (!confirm("¿Estás seguro de que deseas eliminar este agente?")) {
        Logger.info('Eliminación cancelada por el usuario');
        return;
    }

    try {
        const response = await fetch(`${getSecureBaseUrl()}/api/v1/agents/${agentId}`, {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
            },
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail);
        }

        Logger.success('Agente eliminado correctamente');
        showNotification("Agente eliminado correctamente.", "success");
        location.reload();
    } catch (error) {
        Logger.error('Error al eliminar agente:', error);
        showNotification(`Error al eliminar agente: ${error.message}`, "error");
    }

    Logger.groupEnd();
}

// Funciones auxiliares para la interfaz

function disableInstallationInterface(submitButton) {
    submitButton.disabled = true;
    submitButton.innerHTML = 'Instalando...';
    document.getElementById('driver').disabled = true;
    document.getElementById('printerIp').disabled = true;
}

function updateInstallationInterface() {
    const closeButton = document.querySelector('button[onclick="closeModal(\'installPrinterModal\')"]');
    if (closeButton) {
        closeButton.textContent = 'Cerrar ventana';
    }
}

function handleInstallationError(error) {
    addLogMessage(`Error: ${error.message}`, 'error');
    const submitButton = document.querySelector('button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = false;
        submitButton.innerHTML = 'Instalar';
    }
    WS_CONFIG.currentInstallation = null;
}

function handleDriverLoadError(error) {
    addLogMessage(`Error al cargar drivers: ${error.message}`, 'error');
    showNotification(`Error al cargar drivers: ${error.message}`, 'error');
}

function resetInstallationForm() {
    const form = document.getElementById('installPrinterForm');
    if (form) {
        form.reset();
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.innerHTML = 'Instalar';
        }
    }
    
    const logMessages = document.getElementById('logMessages');
    if (logMessages) {
        logMessages.innerHTML = '';
        addLogMessage('Iniciando proceso de instalación...', 'info');
    }
}

function showLoadingState(content) {
    content.innerHTML = `
        <div class="flex justify-center items-center p-8">
            <i class="fas fa-circle-notch fa-spin text-blue-500 text-3xl mr-3"></i>
            <span class="text-gray-600 text-lg">Cargando información...</span>
        </div>
    `;
}

function handleAgentInfoError(content, error) {
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

// Función para cerrar modales
function closeModal(modalId) {
    Logger.group('Cerrando Modal');

    try {
        const modal = document.getElementById(modalId);
        if (!modal) {
            Logger.warning('Modal no encontrado:', modalId);
            return;
        }

        // Verificar instalación en progreso
        if (modalId === 'installPrinterModal' && WS_CONFIG.currentInstallation) {
            const installationTime = (new Date() - WS_CONFIG.currentInstallation.startTime) / 1000;
            if (installationTime < 60) {
                if (!confirm('La instalación está en progreso. ¿Está seguro que desea cerrar la ventana?')) {
                    Logger.info('Cierre de modal cancelado por el usuario');
                    return;
                }
            }
        }

        modal.classList.add('hidden');
        
        // Limpieza adicional para el modal de instalación
        if (modalId === 'installPrinterModal') {
            const form = document.getElementById('installPrinterForm');
            if (form) form.reset();
            WS_CONFIG.currentInstallation = null;
            const logMessages = document.getElementById('logMessages');
            if (logMessages) logMessages.innerHTML = '';
        }

        Logger.success('Modal cerrado correctamente:', modalId);
    } catch (error) {
        Logger.error('Error al cerrar modal:', error);
    }

    Logger.groupEnd();
}