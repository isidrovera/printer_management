// static/js/printer-oids.js

// Variables globales
let testConfigInterval;

// Funciones para el manejo del modal de prueba
function testConfig(configId) {
    const modal = document.getElementById('testConfigModal');
    document.getElementById('testConfigId').value = configId;
    modal.classList.remove('hidden');
    // Limpiar resultados previos
    document.getElementById('testResults').innerHTML = '';
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    modal.classList.add('hidden');
    if (testConfigInterval) {
        clearInterval(testConfigInterval);
    }
}

function addTestResult(message, type = 'info') {
    const resultsDiv = document.getElementById('testResults');
    const messageDiv = document.createElement('div');
    messageDiv.className = `flex items-center space-x-2 ${type === 'error' ? 'text-red-600' : type === 'success' ? 'text-green-600' : 'text-gray-600'}`;
    
    // Agregar icono según el tipo de mensaje
    const icon = document.createElement('i');
    icon.className = `fas fa-${type === 'error' ? 'times-circle' : type === 'success' ? 'check-circle' : 'info-circle'} w-4`;
    messageDiv.appendChild(icon);
    
    const textSpan = document.createElement('span');
    textSpan.textContent = message;
    messageDiv.appendChild(textSpan);
    
    resultsDiv.appendChild(messageDiv);
    resultsDiv.scrollTop = resultsDiv.scrollHeight;
}

// Funciones para el manejo de OIDs
function addOidGroup() {
    const template = document.getElementById('oidGroupTemplate');
    const oidGroups = document.getElementById('oidGroups');
    const newGroup = template.content.cloneNode(true);
    oidGroups.appendChild(newGroup);
}

function removeOidGroup(button) {
    if (confirm('¿Está seguro de eliminar este grupo de OIDs?')) {
        const group = button.closest('.oid-group');
        group.remove();
    }
}

function addOid(button) {
    const template = document.getElementById('oidEntryTemplate');
    const oidList = button.previousElementSibling;
    const newEntry = template.content.cloneNode(true);
    oidList.appendChild(newEntry);
}

function removeOid(button) {
    const entry = button.closest('.oid-entry');
    entry.remove();
}

// Función para eliminar una configuración
async function deleteConfig(configId) {
    if (!confirm('¿Está seguro de eliminar esta configuración?')) {
        return;
    }

    try {
        const response = await fetch(`/printer-oids/${configId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Error al eliminar la configuración');
        }

        showNotification('Configuración eliminada exitosamente', 'success');
        // Recargar la página después de eliminar
        window.location.reload();

    } catch (error) {
        console.error('Error:', error);
        showNotification(error.message, 'error');
    }
}

// Función para probar la configuración
async function handleTestConfig(event) {
    event.preventDefault();
    const formData = {
        config_id: document.getElementById('testConfigId').value,
        printer_ip: document.getElementById('testPrinterIp').value
    };

    try {
        addTestResult('Iniciando prueba de configuración...');
        const response = await fetch('/api/v1/printer-oids/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.detail || 'Error al probar la configuración');
        }

        // Procesar resultados
        result.results.forEach(item => {
            const status = item.success ? 'success' : 'error';
            const message = `${item.oid_name}: ${item.value || item.error}`;
            addTestResult(message, status);
        });

        addTestResult('Prueba completada', 'success');

    } catch (error) {
        console.error('Error:', error);
        addTestResult(`Error: ${error.message}`, 'error');
    }
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    
    notification.className = `flex items-center p-4 rounded-lg shadow-lg ${
        type === 'success' ? 'bg-green-100 text-green-800' :
        type === 'error' ? 'bg-red-100 text-red-800' :
        'bg-blue-100 text-blue-800'
    }`;

    const icon = document.createElement('i');
    icon.className = `fas fa-${
        type === 'success' ? 'check-circle' :
        type === 'error' ? 'exclamation-circle' :
        'info-circle'
    } mr-2`;
    
    notification.appendChild(icon);
    notification.insertAdjacentText('beforeend', message);
    
    container.appendChild(notification);

    // Remover la notificación después de 5 segundos
    setTimeout(() => {
        notification.remove();
    }, 5000);
}

// Función para inicializar la búsqueda
function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const brand = row.querySelector('td:nth-child(1)').textContent.toLowerCase();
                const model = row.querySelector('td:nth-child(2)').textContent.toLowerCase();
                const shouldShow = brand.includes(searchTerm) || model.includes(searchTerm);
                row.classList.toggle('hidden', !shouldShow);
            });
        });
    }
}

// Inicialización cuando el DOM está listo
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar formulario de prueba
    const testForm = document.getElementById('testConfigForm');
    if (testForm) {
        testForm.addEventListener('submit', handleTestConfig);
    }

    // Inicializar búsqueda
    initializeSearch();

    // Inicializar versión SNMP
    const snmpVersion = document.getElementById('snmp_version');
    if (snmpVersion) {
        snmpVersion.addEventListener('change', function() {
            const snmpv3Config = document.getElementById('snmpv3Config');
            const snmpv1v2Fields = document.querySelectorAll('.snmp-v1-v2');
            
            if (this.value === '3') {
                snmpv3Config.classList.remove('hidden');
                snmpv1v2Fields.forEach(field => field.classList.add('hidden'));
            } else {
                snmpv3Config.classList.add('hidden');
                snmpv1v2Fields.forEach(field => field.classList.remove('hidden'));
            }
        });

        // Trigger inicial
        snmpVersion.dispatchEvent(new Event('change'));
    }

    // Si no hay grupos de OIDs, agregar uno por defecto
    const oidGroups = document.getElementById('oidGroups');
    if (oidGroups && !oidGroups.hasChildNodes()) {
        addOidGroup();
    }
});