// static/js/agents.js
// Configuración global y estado
const APP_CONFIG = {
    DEBUG: false, // Cambiar a true para ver logs detallados
    API_VERSION: 'v1',
    NOTIFICATION_TIMEOUT: 5000,
    MAX_LOG_MESSAGES: 50
};

const WS_CONFIG = {
    protocol: window.location.protocol === 'https:' ? 'wss:' : 'ws:',
    host: window.location.host,
    path: '/api/v1/ws/status',
    reconnectInterval: 1000,
    maxReconnectAttempts: 10,
    currentInstallation: null
};

// Variables globales
let wsConnection = null;
let reconnectAttempts = 0;
let isReconnecting = false;
let currentAgentToken = '';
let agentToDelete = null;

// Utilidades de logging
const Logger = {
    debug: (...args) => {
        if (APP_CONFIG.DEBUG) {
            console.debug('[DEBUG]', ...args);
        }
    },
    info: (...args) => console.log('[INFO]', ...args),
    warn: (...args) => console.warn('[WARN]', ...args),
    error: (...args) => console.error('[ERROR]', ...args),
    group: (name) => {
        if (APP_CONFIG.DEBUG) {
            console.group(name);
        }
    },
    groupEnd: () => {
        if (APP_CONFIG.DEBUG) {
            console.groupEnd();
        }
    }
};

// Utilidad para manejar errores
class AppError extends Error {
    constructor(message, type = 'error', details = null) {
        super(message);
        this.name = 'AppError';
        this.type = type;
        this.details = details;
        this.timestamp = new Date();
    }

    static handle(error, context = '') {
        const message = error.message || 'Error desconocido';
        Logger.error(`${context}: ${message}`, error);
        
        if (error instanceof AppError) {
            showNotification(message, error.type);
            addLogMessage(message, error.type);
        } else {
            showNotification(message, 'error');
            addLogMessage(message, 'error');
        }
    }
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    Logger.info(`Notificación [${type}]: ${message}`);
    
    const notificationContainer = document.getElementById('notification-container');
    if (!notificationContainer) {
        Logger.error('Container de notificaciones no encontrado');
        return;
    }

    const notification = document.createElement('div');
    notification.classList.add('notification', `notification-${type}`, 'animate-fade-in');
    
    // Clases de Tailwind para estilos
    notification.classList.add(
        'fixed', 'top-4', 'right-4', 'p-4', 'rounded-lg', 'shadow-lg',
        'max-w-md', 'z-50', 'flex', 'items-center', 'justify-between',
        type === 'error' ? 'bg-red-100 text-red-800' :
        type === 'success' ? 'bg-green-100 text-green-800' :
        type === 'warning' ? 'bg-yellow-100 text-yellow-800' :
        'bg-blue-100 text-blue-800'
    );

    notification.innerHTML = `
        <div class="flex items-center">
            <i class="fas fa-${
                type === 'error' ? 'exclamation-circle' :
                type === 'success' ? 'check-circle' :
                type === 'warning' ? 'exclamation-triangle' :
                'info-circle'
            } mr-3"></i>
            <span>${message}</span>
        </div>
        <button class="ml-4 hover:text-gray-600 focus:outline-none">
            <i class="fas fa-times"></i>
        </button>
    `;

    // Evento para cerrar la notificación
    const closeButton = notification.querySelector('button');
    closeButton.addEventListener('click', () => {
        notification.classList.add('animate-fade-out');
        setTimeout(() => notification.remove(), 300);
    });

    notificationContainer.appendChild(notification);

    // Auto-cerrar después de un tiempo
    setTimeout(() => {
        if (notification.parentElement) {
            notification.classList.add('animate-fade-out');
            setTimeout(() => notification.remove(), 300);
        }
    }, APP_CONFIG.NOTIFICATION_TIMEOUT);
}

// Función para añadir mensajes al log
function addLogMessage(message, type = 'info') {
    const logContainer = document.getElementById('logMessages');
    if (!logContainer) {
        Logger.error('Container de logs no encontrado');
        return;
    }

    const logEntry = document.createElement('div');
    const timestamp = new Date().toLocaleTimeString();
    
    // Determinar clases y símbolo según el tipo
    let classes = 'py-2 px-3 rounded mb-1 animate-fade-in';
    let symbol = '';
    
    switch (type) {
        case 'success':
            classes += ' bg-green-50 text-green-700';
            symbol = '✓';
            break;
        case 'error':
            classes += ' bg-red-50 text-red-700';
            symbol = '✗';
            break;
        case 'warning':
            classes += ' bg-yellow-50 text-yellow-700';
            symbol = '⚠';
            break;
        default:
            classes += ' bg-gray-50 text-gray-700';
            symbol = 'ℹ';
    }

    logEntry.className = classes;
    logEntry.innerHTML = `
        <div class="flex items-center">
            <span class="text-xs text-gray-500 mr-2">${timestamp}</span>
            <span class="mr-2">${symbol}</span>
            <span>${message}</span>
        </div>
    `;
    
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;

    // Mantener solo los últimos N mensajes
    while (logContainer.children.length > APP_CONFIG.MAX_LOG_MESSAGES) {
        logContainer.removeChild(logContainer.firstChild);
    }
}

// Función para cargar recursos externos (CSS, fuentes, etc.)
async function loadExternalResources() {
    try {
        // Cargar Font Awesome
        const fontAwesome = document.createElement('link');
        fontAwesome.rel = 'stylesheet';
        fontAwesome.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css';
        
        // Precargar la fuente
        const fontPreload = document.createElement('link');
        fontPreload.rel = 'preload';
        fontPreload.as = 'font';
        fontPreload.type = 'font/woff2';
        fontPreload.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/webfonts/fa-solid-900.woff2';
        fontPreload.crossOrigin = 'anonymous';

        // Agregar al documento
        document.head.appendChild(fontPreload);
        document.head.appendChild(fontAwesome);

        // Esperar a que las fuentes estén cargadas
        await document.fonts.ready;
        Logger.info('Recursos externos cargados correctamente');
        
    } catch (error) {
        throw new AppError('Error al cargar recursos externos', 'error', error);
    }
}
// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', async function() {
    try {
        Logger.group('Inicialización de la aplicación');
        
        // Cargar recursos externos primero
        await loadExternalResources();
        
        // Inicializar componentes principales
        await initializeWebSocket();
        initializeSearchFilter();
        initializeFormHandlers();
        await initializeDriverSelect();
        
        Logger.info('Aplicación inicializada correctamente');
        Logger.groupEnd();
    } catch (error) {
        AppError.handle(error, 'Inicialización de la aplicación');
        Logger.groupEnd();
    }
});

// Función mejorada para inicializar WebSocket
async function initializeWebSocket() {
    if (wsConnection && (wsConnection.readyState === WebSocket.CONNECTING || wsConnection.readyState === WebSocket.OPEN)) {
        Logger.debug('Conexión WebSocket ya existe');
        return;
    }

    try {
        Logger.group('Inicialización WebSocket');
        const wsUrl = `${WS_CONFIG.protocol}//${WS_CONFIG.host}${WS_CONFIG.path}`;
        Logger.info('Intentando conectar WebSocket a:', wsUrl);

        wsConnection = new WebSocket(wsUrl);
        
        // Configurar manejadores de eventos
        wsConnection.onopen = handleWebSocketOpen;
        wsConnection.onmessage = handleWebSocketMessage;
        wsConnection.onclose = handleWebSocketClose;
        wsConnection.onerror = handleWebSocketError;

        // Esperar a que la conexión se establezca o falle
        await new Promise((resolve, reject) => {
            const timeout = setTimeout(() => {
                reject(new AppError('Timeout al conectar WebSocket', 'error'));
            }, 5000);

            wsConnection.addEventListener('open', () => {
                clearTimeout(timeout);
                resolve();
            });

            wsConnection.addEventListener('error', (error) => {
                clearTimeout(timeout);
                reject(new AppError('Error al conectar WebSocket', 'error', error));
            });
        });

        Logger.groupEnd();
    } catch (error) {
        Logger.groupEnd();
        throw new AppError('Error al inicializar WebSocket', 'error', error);
    }
}

// Manejador de apertura de WebSocket
function handleWebSocketOpen() {
    Logger.info('✅ WebSocket conectado exitosamente');
    reconnectAttempts = 0;
    isReconnecting = false;
    
    showNotification('Conexión establecida con el servidor', 'success');
    addLogMessage('Conexión establecida con el servidor', 'success');

    // Enviar mensaje de inicialización si es necesario
    const initMessage = {
        type: 'init',
        timestamp: new Date().toISOString()
    };
    
    try {
        wsConnection.send(JSON.stringify(initMessage));
        Logger.debug('Mensaje de inicialización enviado');
    } catch (error) {
        AppError.handle(error, 'Error al enviar mensaje de inicialización');
    }
}

// Manejador de mensajes de WebSocket
function handleWebSocketMessage(event) {
    try {
        Logger.group('Mensaje WebSocket Recibido');
        Logger.debug('Mensaje raw:', event.data);

        // Verificar si es un mensaje de log del agente
        if (typeof event.data === 'string' && event.data.startsWith('Agent')) {
            Logger.debug('Mensaje de log del agente:', event.data);
            handleAgentLogMessage(event.data);
            Logger.groupEnd();
            return;
        }

        // Intentar parsear como JSON
        let data;
        try {
            data = JSON.parse(event.data);
            Logger.debug('JSON parseado correctamente:', data);
        } catch (parseError) {
            Logger.warn('No se pudo parsear como JSON:', {
                error: parseError,
                rawData: event.data.slice(0, 100) + (event.data.length > 100 ? '...' : '')
            });
            handleAgentLogMessage(event.data);
            Logger.groupEnd();
            return;
        }

        // Procesar mensaje JSON según su tipo
        if (data && data.type) {
            Logger.debug(`Procesando mensaje de tipo: ${data.type}`);
            processJsonMessage(data);
        } else {
            Logger.debug('Mensaje JSON sin tipo específico:', data);
        }

        Logger.groupEnd();
    } catch (error) {
        Logger.groupEnd();
        AppError.handle(error, 'Error procesando mensaje WebSocket');
    }
}

// Manejador de cierre de WebSocket
function handleWebSocketClose(event) {
    Logger.warn('⚠️ WebSocket cerrado. Código:', event.code);
    showNotification('Conexión perdida con el servidor', 'warning');

    // Verificar si debemos intentar reconectar
    if (!isReconnecting && reconnectAttempts < WS_CONFIG.maxReconnectAttempts) {
        isReconnecting = true;
        reconnectAttempts++;
        
        Logger.info(`Intento de reconexión ${reconnectAttempts} de ${WS_CONFIG.maxReconnectAttempts}`);
        addLogMessage(`Reintentando conexión (${reconnectAttempts}/${WS_CONFIG.maxReconnectAttempts})...`, 'warning');
        
        setTimeout(async () => {
            try {
                await initializeWebSocket();
                isReconnecting = false;
            } catch (error) {
                isReconnecting = false;
                AppError.handle(error, 'Error durante la reconexión');
            }
        }, WS_CONFIG.reconnectInterval * reconnectAttempts); // Backoff exponencial
    } else if (reconnectAttempts >= WS_CONFIG.maxReconnectAttempts) {
        const error = new AppError(
            'No se pudo restablecer la conexión con el servidor',
            'error',
            { code: event.code, attempts: reconnectAttempts }
        );
        AppError.handle(error);
    }
}

// Manejador de errores de WebSocket
function handleWebSocketError(error) {
    Logger.error('❌ Error en WebSocket:', error);
    AppError.handle(new AppError('Error en la conexión con el servidor', 'error', error));
}

// Procesar diferentes tipos de mensajes JSON
function processJsonMessage(data) {
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
                Logger.debug('Mensaje recibido sin tipo específico:', data);
        }
    } catch (error) {
        AppError.handle(error, 'Error procesando mensaje JSON');
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
// Funciones de actualización de estado del agente
function updateAgentStatus(data) {
    try {
        Logger.group('Actualización Estado Agente');
        Logger.debug('Datos recibidos:', data);

        const agentElement = document.querySelector(`[data-agent-id="${data.agent_id}"]`);
        if (!agentElement) {
            throw new AppError('Elemento del agente no encontrado', 'warning');
        }

        // Actualizar estado
        const statusElement = agentElement.querySelector('.agent-status');
        if (statusElement) {
            updateStatusElement(statusElement, data.status);
        }

        // Actualizar última actividad
        const lastActivityElement = agentElement.querySelector('.last-activity');
        if (lastActivityElement) {
            lastActivityElement.textContent = new Date().toLocaleString();
        }

        // Actualizar indicadores visuales
        updateAgentVisualIndicators(agentElement, data);

        Logger.debug('✅ Estado del agente actualizado');
        Logger.groupEnd();
    } catch (error) {
        Logger.groupEnd();
        AppError.handle(error, 'Error al actualizar estado del agente');
    }
}

// Actualizar indicadores visuales del agente
function updateAgentVisualIndicators(agentElement, data) {
    // Actualizar icono de estado
    const statusIcon = agentElement.querySelector('.status-icon');
    if (statusIcon) {
        const iconClass = getStatusIconClass(data.status);
        statusIcon.className = `status-icon fas ${iconClass} mr-2`;
    }

    // Actualizar color de fondo según estado
    const statusClasses = {
        online: 'bg-green-50 border-green-200',
        offline: 'bg-red-50 border-red-200',
        warning: 'bg-yellow-50 border-yellow-200',
        installing: 'bg-blue-50 border-blue-200'
    };

    // Remover clases anteriores y agregar nuevas
    Object.values(statusClasses).forEach(className => {
        const classes = className.split(' ');
        classes.forEach(cls => agentElement.classList.remove(cls));
    });

    if (statusClasses[data.status]) {
        const newClasses = statusClasses[data.status].split(' ');
        newClasses.forEach(cls => agentElement.classList.add(cls));
    }
}

// Actualizar elemento de estado
function updateStatusElement(element, status) {
    // Definir clases y texto según estado
    const statusConfig = {
        online: {
            classes: 'text-green-700 bg-green-100',
            text: 'En línea'
        },
        offline: {
            classes: 'text-red-700 bg-red-100',
            text: 'Desconectado'
        },
        warning: {
            classes: 'text-yellow-700 bg-yellow-100',
            text: 'Advertencia'
        },
        installing: {
            classes: 'text-blue-700 bg-blue-100',
            text: 'Instalando'
        }
    };

    // Limpiar clases anteriores
    element.className = 'agent-status px-2 py-1 rounded-full text-sm font-medium';

    // Agregar nuevas clases
    if (statusConfig[status]) {
        element.classList.add(...statusConfig[status].classes.split(' '));
        element.textContent = statusConfig[status].text;
    } else {
        element.classList.add('text-gray-700', 'bg-gray-100');
        element.textContent = 'Estado desconocido';
    }
}

// Obtener clase de icono según estado
function getStatusIconClass(status) {
    const iconClasses = {
        online: 'fa-check-circle text-green-500',
        offline: 'fa-times-circle text-red-500',
        warning: 'fa-exclamation-triangle text-yellow-500',
        installing: 'fa-spinner fa-spin text-blue-500'
    };

    return iconClasses[status] || 'fa-question-circle text-gray-500';
}

// Función para mostrar información detallada del agente
async function showAgentInfo(agentId) {
    try {
        Logger.group('Mostrando información del agente');
        Logger.debug('ID del agente:', agentId);

        const modal = document.getElementById('agentInfoModal');
        const content = document.getElementById('agentInfoContent');

        if (!modal || !content) {
            throw new AppError('Elementos del modal no encontrados');
        }

        // Mostrar modal con estado de carga
        modal.classList.remove('hidden');
        showLoadingState(content);

        // Obtener datos del agente
        const response = await fetch(`/api/v1/agents/${agentId}`);
        if (!response.ok) {
            throw new AppError(`Error al cargar los datos: ${response.status}`);
        }

        const agent = await response.json();
        Logger.debug('Datos del agente recibidos:', agent);

        // Actualizar contenido del modal
        updateAgentInfoContent(content, agent);

        Logger.groupEnd();
    } catch (error) {
        Logger.groupEnd();
        AppError.handle(error, 'Error al mostrar información del agente');
        showErrorState(content, error.message);
    }
}

// Mostrar estado de carga en el modal
function showLoadingState(container) {
    container.innerHTML = `
        <div class="flex justify-center items-center p-8">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <span class="ml-3 text-gray-600">Cargando información...</span>
        </div>
    `;
}

// Mostrar estado de error en el modal
function showErrorState(container, message) {
    container.innerHTML = `
        <div class="text-center py-8">
            <div class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-red-100 mb-4">
                <i class="fas fa-exclamation-circle text-red-500 text-2xl"></i>
            </div>
            <h3 class="text-lg font-medium text-gray-900 mb-2">Error al cargar la información</h3>
            <p class="text-sm text-gray-500">${message}</p>
        </div>
    `;
}

// Actualizar contenido del modal con información del agente
function updateAgentInfoContent(container, agent) {
    // Implementar el HTML completo del modal con la información del agente
    container.innerHTML = `
        <div class="grid grid-cols-2 gap-6 p-4">
            <!-- Información Básica -->
            <div class="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
                <h2 class="text-lg font-semibold text-gray-900 mb-4">
                    <i class="fas fa-info-circle text-blue-500 mr-2"></i>
                    Información Básica
                </h2>
                ${generateBasicInfoHTML(agent)}
            </div>

            <!-- Sistema Operativo -->
            <div class="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
                <h2 class="text-lg font-semibold text-gray-900 mb-4">
                    <i class="fas fa-desktop text-blue-500 mr-2"></i>
                    Sistema Operativo
                </h2>
                ${generateSystemInfoHTML(agent)}
            </div>

            <!-- Hardware -->
            <div class="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
                <h2 class="text-lg font-semibold text-gray-900 mb-4">
                    <i class="fas fa-microchip text-blue-500 mr-2"></i>
                    Hardware
                </h2>
                ${generateHardwareInfoHTML(agent)}
            </div>

            <!-- Red -->
            <div class="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
                <h2 class="text-lg font-semibold text-gray-900 mb-4">
                    <i class="fas fa-network-wired text-blue-500 mr-2"></i>
                    Información de Red
                </h2>
                ${generateNetworkInfoHTML(agent)}
            </div>
        </div>
    `;
}

// Generar HTML para información básica
function generateBasicInfoHTML(agent) {
    return `
        <div class="space-y-4">
            <div class="flex items-center">
                <div class="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                    <i class="fas fa-desktop text-blue-500"></i>
                </div>
                <div class="ml-3">
                    <span class="text-sm text-gray-500">Hostname</span>
                    <p class="font-medium">${agent.hostname}</p>
                </div>
            </div>
            <!-- Más información básica... -->
        </div>
    `;
}

// Generar HTML para información del sistema
function generateSystemInfoHTML(agent) {
    return `
        <div class="space-y-4">
            <div class="flex items-center">
                <div class="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
                    <i class="fas fa-cog text-purple-500"></i>
                </div>
                <div class="ml-3">
                    <span class="text-sm text-gray-500">Sistema Operativo</span>
                    <p class="font-medium">${agent.system_info.Sistema["Nombre del SO"]}</p>
                </div>
            </div>
            <!-- Más información del sistema... -->
        </div>
    `;
}

// Función mejorada para inicializar el select de drivers
async function initializeDriverSelect() {
    const driverSelect = document.getElementById('driver');
    if (!driverSelect) {
        Logger.warn('Elemento select de drivers no encontrado');
        return;
    }

    try {
        Logger.group('Inicialización de drivers');
        addLogMessage('Cargando lista de drivers...', 'info');
        
        const protocol = window.location.protocol;
        const host = window.location.host;
        const url = `${protocol}//${host}/api/${APP_CONFIG.API_VERSION}/drivers`;
        
        Logger.debug('Solicitando drivers desde:', url);

        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            },
            credentials: 'same-origin'
        });

        if (!response.ok) {
            throw new AppError(`Error HTTP: ${response.status}`);
        }

        const drivers = await response.json();
        validateDriversData(drivers);
        
        populateDriverSelect(driverSelect, drivers);
        addLogMessage('Drivers cargados correctamente', 'success');
        Logger.groupEnd();

    } catch (error) {
        Logger.groupEnd();
        throw new AppError('Error al inicializar drivers', 'error', error);
    }
}

// Validar datos de drivers
function validateDriversData(drivers) {
    if (!Array.isArray(drivers)) {
        throw new AppError('Formato de datos de drivers inválido');
    }

    const requiredFields = ['id', 'manufacturer', 'model', 'driver_filename'];
    const invalidDrivers = drivers.filter(driver => 
        !requiredFields.every(field => driver.hasOwnProperty(field))
    );

    if (invalidDrivers.length > 0) {
        Logger.warn('Drivers con campos faltantes:', invalidDrivers);
        throw new AppError('Algunos drivers tienen campos requeridos faltantes');
    }
}

// Poblar el select de drivers
function populateDriverSelect(select, drivers) {
    select.innerHTML = '<option value="">Seleccione un driver</option>';
    
    const sortedDrivers = drivers.sort((a, b) => 
        `${a.manufacturer} ${a.model}`.localeCompare(`${b.manufacturer} ${b.model}`)
    );

    sortedDrivers.forEach((driver) => {
        const option = document.createElement('option');
        option.value = driver.id;
        option.textContent = `${driver.manufacturer} - ${driver.model} (${driver.driver_filename})`;
        select.appendChild(option);
    });
}

// Función para mostrar el modal de instalación de impresora
function showInstallPrinter(agentToken) {
    try {
        Logger.group('Mostrar modal de instalación');
        Logger.debug('Token del agente:', agentToken);

        currentAgentToken = agentToken;
        
        const modal = document.getElementById('installPrinterModal');
        if (!modal) {
            throw new AppError('Modal de instalación no encontrado');
        }

        // Mostrar modal y resetear estado
        modal.classList.remove('hidden');
        resetInstallationForm();
        
        // Limpiar logs anteriores
        const logMessages = document.getElementById('logMessages');
        if (logMessages) {
            logMessages.innerHTML = '';
            addLogMessage('Iniciando proceso de instalación...', 'info');
        }
        
        // Cargar drivers
        initializeDriverSelect();
        
        Logger.groupEnd();
    } catch (error) {
        Logger.groupEnd();
        AppError.handle(error, 'Error al mostrar modal de instalación');
    }
}

// Resetear formulario de instalación
function resetInstallationForm() {
    const form = document.getElementById('installPrinterForm');
    if (!form) return;

    form.reset();
    
    // Habilitar campos y botones
    const elements = ['driver', 'printerIp'];
    elements.forEach(id => {
        const element = document.getElementById(id);
        if (element) element.disabled = false;
    });

    const submitButton = form.querySelector('button[type="submit"]');
    if (submitButton) {
        submitButton.disabled = false;
        submitButton.innerHTML = 'Instalar';
    }
}

// Función para manejar la instalación de impresora
async function handlePrinterInstallation(event) {
    event.preventDefault();
    
    const form = event.target;
    const submitButton = form.querySelector('button[type="submit"]');
    
    try {
        Logger.group('Instalación de impresora');
        
        // Validar campos
        const driverId = document.getElementById('driver').value;
        const printerIp = document.getElementById('printerIp').value;

        if (!driverId || !printerIp) {
            throw new AppError('Por favor complete todos los campos');
        }

        // Validar formato IP
        if (!isValidIpAddress(printerIp)) {
            throw new AppError('Dirección IP inválida');
        }

        // Guardar información de la instalación actual
        WS_CONFIG.currentInstallation = {
            driverId,
            printerIp,
            startTime: new Date()
        };

        // Actualizar UI
        updateUIForInstallation(true);
        
        // Enviar solicitud de instalación
        const response = await sendInstallationRequest(driverId, printerIp);
        
        // Procesar respuesta
        await handleInstallationResponse(response);
        
        Logger.groupEnd();

    } catch (error) {
        Logger.groupEnd();
        AppError.handle(error, 'Error en la instalación');
        updateUIForInstallation(false);
    }
}

// Validar dirección IP
function isValidIpAddress(ip) {
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/;
    if (!ipRegex.test(ip)) return false;
    
    const parts = ip.split('.');
    return parts.every(part => {
        const num = parseInt(part, 10);
        return num >= 0 && num <= 255;
    });
}

// Actualizar UI durante la instalación
function updateUIForInstallation(installing) {
    const form = document.getElementById('installPrinterForm');
    const submitButton = form.querySelector('button[type="submit"]');
    const closeButton = document.querySelector('button[onclick="closeModal(\'installPrinterModal\')"]');
    
    if (installing) {
        // Deshabilitar campos y cambiar textos
        document.getElementById('driver').disabled = true;
        document.getElementById('printerIp').disabled = true;
        submitButton.disabled = true;
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Instalando...';
        if (closeButton) closeButton.textContent = 'Cerrar ventana';
    } else {
        // Reactivar campos
        document.getElementById('driver').disabled = false;
        document.getElementById('printerIp').disabled = false;
        submitButton.disabled = false;
        submitButton.innerHTML = 'Instalar';
    }
}

// Enviar solicitud de instalación
async function sendInstallationRequest(driverId, printerIp) {
    const response = await fetch(`/api/${APP_CONFIG.API_VERSION}/printers/install/${currentAgentToken}`, {
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
        throw new AppError(errorData.detail || `Error en la instalación: ${response.status}`);
    }

    return response;
}

// Manejar respuesta de instalación
async function handleInstallationResponse(response) {
    const data = await response.json();
    addLogMessage('Comando de instalación enviado correctamente', 'success');
    addLogMessage('La instalación continúa en segundo plano...', 'info');
    
    return data;
}

// Actualizar estado de impresora
function updatePrinterStatus(data) {
    try {
        Logger.group('Actualización Estado Impresora');
        Logger.debug('Datos recibidos:', data);

        const printerElement = document.querySelector(`[data-printer-id="${data.printer_id}"]`);
        if (!printerElement) {
            throw new AppError('Elemento de impresora no encontrado', 'warning');
        }

        updatePrinterStatusElement(printerElement, data);
        Logger.debug('Estado de impresora actualizado');
        Logger.groupEnd();

    } catch (error) {
        Logger.groupEnd();
        AppError.handle(error, 'Error al actualizar estado de impresora');
    }
}

// Actualizar elemento de estado de impresora
function updatePrinterStatusElement(element, data) {
    const statusElement = element.querySelector('.printer-status');
    if (statusElement) {
        const statusConfig = {
            online: { class: 'bg-green-100 text-green-800', text: 'Conectada' },
            offline: { class: 'bg-red-100 text-red-800', text: 'Desconectada' },
            error: { class: 'bg-yellow-100 text-yellow-800', text: 'Error' },
            installing: { class: 'bg-blue-100 text-blue-800', text: 'Instalando' }
        };

        const status = statusConfig[data.status] || statusConfig.error;
        
        statusElement.className = `printer-status px-2 py-1 rounded-full text-sm font-medium ${status.class}`;
        statusElement.textContent = status.text;
    }

    // Actualizar otros elementos si existen
    updatePrinterDetails(element, data);
}

// Actualizar detalles adicionales de la impresora
function updatePrinterDetails(element, data) {
    // Actualizar modelo
    const modelElement = element.querySelector('.printer-model');
    if (modelElement && data.model) {
        modelElement.textContent = data.model;
    }

    // Actualizar dirección IP
    const ipElement = element.querySelector('.printer-ip');
    if (ipElement && data.ip) {
        ipElement.textContent = data.ip;
    }

    // Actualizar última actualización
    const lastUpdateElement = element.querySelector('.last-update');
    if (lastUpdateElement) {
        lastUpdateElement.textContent = new Date().toLocaleString();
    }
}
// Inicializar filtro de búsqueda
function initializeSearchFilter() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) {
        Logger.warn('Elemento de búsqueda no encontrado');
        return;
    }

    searchInput.addEventListener('input', debounce(function(e) {
        try {
            const searchTerm = e.target.value.toLowerCase().trim();
            filterTableRows(searchTerm);
        } catch (error) {
            AppError.handle(error, 'Error al filtrar resultados');
        }
    }, 300));
}

// Función de debounce para optimizar búsqueda
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Filtrar filas de la tabla
function filterTableRows(searchTerm) {
    const rows = document.querySelectorAll('tbody tr');
    let matchCount = 0;

    rows.forEach((row) => {
        const text = row.textContent.toLowerCase();
        const shouldShow = text.includes(searchTerm);
        row.style.display = shouldShow ? '' : 'none';
        if (shouldShow) matchCount++;
    });

    updateSearchResults(matchCount, rows.length);
}

// Actualizar resultados de búsqueda
function updateSearchResults(matchCount, totalCount) {
    const resultsElement = document.getElementById('searchResults');
    if (resultsElement) {
        resultsElement.textContent = `Mostrando ${matchCount} de ${totalCount} resultados`;
    }
}

// Función para cerrar modales
function closeModal(modalId) {
    try {
        Logger.group('Cerrando modal');
        Logger.debug('ID del modal:', modalId);

        const modal = document.getElementById(modalId);
        if (!modal) {
            throw new AppError('Modal no encontrado');
        }

        // Verificar si hay una instalación en progreso
        if (modalId === 'installPrinterModal' && WS_CONFIG.currentInstallation) {
            const installationTime = (new Date() - WS_CONFIG.currentInstallation.startTime) / 1000;
            
            if (installationTime < 60) {
                const confirm = window.confirm('La instalación está en progreso. ¿Está seguro que desea cerrar la ventana?');
                if (!confirm) {
                    Logger.debug('Cierre de modal cancelado por el usuario');
                    Logger.groupEnd();
                    return;
                }
            }
        }

        // Limpiar el modal según su tipo
        cleanupModal(modal, modalId);
        
        // Ocultar el modal
        modal.classList.add('hidden');
        Logger.debug('Modal cerrado exitosamente');
        Logger.groupEnd();

    } catch (error) {
        Logger.groupEnd();
        AppError.handle(error, 'Error al cerrar modal');
    }
}

// Limpiar modal según su tipo
function cleanupModal(modal, modalId) {
    switch (modalId) {
        case 'installPrinterModal':
            cleanupInstallModal(modal);
            break;
        case 'agentInfoModal':
            cleanupAgentInfoModal(modal);
            break;
        default:
            Logger.debug('Tipo de modal no específico, realizando limpieza general');
            modal.querySelectorAll('input, select').forEach(element => {
                element.value = '';
                element.disabled = false;
            });
    }
}

// Limpiar modal de instalación
function cleanupInstallModal(modal) {
    const form = modal.querySelector('#installPrinterForm');
    if (form) {
        form.reset();
        form.querySelectorAll('input, select').forEach(element => {
            element.disabled = false;
        });
    }

    const logMessages = modal.querySelector('#logMessages');
    if (logMessages) {
        logMessages.innerHTML = '';
    }

    WS_CONFIG.currentInstallation = null;
}

// Limpiar modal de información de agente
function cleanupAgentInfoModal(modal) {
    const content = modal.querySelector('#agentInfoContent');
    if (content) {
        content.innerHTML = '';
    }
}

// Función para eliminar un agente
async function deleteAgent(agentId) {
    try {
        Logger.group('Eliminando agente');
        Logger.debug('ID del agente:', agentId);

        if (!await confirmDeletion()) {
            Logger.debug('Eliminación cancelada por el usuario');
            Logger.groupEnd();
            return;
        }

        await performAgentDeletion(agentId);
        
        // Recargar la página después de eliminar
        window.location.reload();
        
        Logger.groupEnd();

    } catch (error) {
        Logger.groupEnd();
        AppError.handle(error, 'Error al eliminar agente');
    }
}

// Confirmar eliminación
function confirmDeletion() {
    return new Promise((resolve) => {
        const result = window.confirm("¿Está seguro de que desea eliminar este agente?");
        resolve(result);
    });
}

// Realizar eliminación del agente
async function performAgentDeletion(agentId) {
    const response = await fetch(`/api/${APP_CONFIG.API_VERSION}/agents/${agentId}`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
        },
    });

    if (!response.ok) {
        const errorData = await response.json();
        throw new AppError(errorData.detail || 'Error al eliminar el agente');
    }

    showNotification("Agente eliminado correctamente", "success");
}

// Inicializar manejadores de formularios
function initializeFormHandlers() {
    const installForm = document.getElementById('installPrinterForm');
    if (installForm) {
        installForm.addEventListener('submit', handlePrinterInstallation);
    }

    // Inicializar otros formularios según sea necesario
    initializeOtherForms();
}

// Inicializar otros formularios
function initializeOtherForms() {
    // Aquí puedes agregar la inicialización de formularios adicionales
    // Por ejemplo, formularios de configuración, búsqueda avanzada, etc.
    Logger.debug('Inicialización de formularios adicionales completada');
}

// Función para manejar errores de red
window.addEventListener('offline', () => {
    showNotification('Conexión a Internet perdida', 'error');
    addLogMessage('Conexión a Internet perdida', 'error');
});

window.addEventListener('online', () => {
    showNotification('Conexión a Internet restaurada', 'success');
    addLogMessage('Conexión a Internet restaurada', 'success');
    
    // Intentar reconectar WebSocket
    if (wsConnection?.readyState !== WebSocket.OPEN) {
        initializeWebSocket();
    }
});

// Limpiar recursos al cerrar la página
window.addEventListener('beforeunload', () => {
    // Cerrar conexión WebSocket si existe
    if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
        wsConnection.close();
    }

    // Limpiar otros recursos si es necesario
    cleanup();
});

// Función de limpieza
function cleanup() {
    // Limpiar timeouts y intervalos
    clearAllTimeouts();
    clearAllIntervals();

    // Limpiar eventos
    removeEventListeners();

    // Limpiar datos de sesión si es necesario
    cleanupSessionData();
}

// Funciones auxiliares de limpieza
function clearAllTimeouts() {
    const highestTimeoutId = setTimeout(() => {}, 0);
    for (let i = 0; i < highestTimeoutId; i++) {
        clearTimeout(i);
    }
}

function clearAllIntervals() {
    const highestIntervalId = setInterval(() => {}, 0);
    for (let i = 0; i < highestIntervalId; i++) {
        clearInterval(i);
    }
}

function removeEventListeners() {
    // Remover event listeners específicos si es necesario
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.removeEventListener('input', () => {});
    }
}

function cleanupSessionData() {
    // Limpiar datos de sesión si es necesario
    WS_CONFIG.currentInstallation = null;
    currentAgentToken = '';
    agentToDelete = null;
}

// Exportar funciones públicas si es necesario
window.showInstallPrinter = showInstallPrinter;
window.closeModal = closeModal;
window.deleteAgent = deleteAgent;
window.showAgentInfo = showAgentInfo;