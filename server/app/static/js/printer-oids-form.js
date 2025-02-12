// static/js/printer-oids-form.js
// Función para logging
function logDebug(message, data = null) {
    const timestamp = new Date().toISOString();
    if (data) {
        console.log(`[${timestamp}] ${message}`, data);
    } else {
        console.log(`[${timestamp}] ${message}`);
    }
}

function getValue(id) {
    const element = document.getElementById(id);
    if (!element) {
        logDebug(`Campo no encontrado: ${id}`);
        return '';
    }
    const value = element.value.trim();
    logDebug(`Valor obtenido para ${id}:`, value);
    return value;
}

function showNotification(message, type = 'info') {
    logDebug('Mostrando notificación:', { message, type });
    
    const container = document.getElementById('notification-container');
    if (!container) {
        logDebug('Contenedor de notificaciones no encontrado');
        return;
    }

    const notification = document.createElement('div');
    notification.className = `fixed top-4 right-4 z-50 flex items-center p-4 rounded-lg shadow-lg ${
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

    setTimeout(() => {
        notification.remove();
        logDebug('Notificación removida');
    }, 5000);
}

document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    
    if (!form) {
        logDebug('Formulario no encontrado');
        return;
    }

    logDebug('Formulario inicializado');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        logDebug('Formulario enviado');
        
        try {
            const formData = {};
            
            // Validación de campos requeridos
            const brand = getValue('brand');
            const modelFamily = getValue('model_family');
            
            if (!brand) {
                throw new Error('El campo Marca es requerido');
            }
            
            if (!modelFamily) {
                throw new Error('El campo Familia de Modelo es requerido');
            }

            // Lista completa de campos
            const fields = [
                // Campos básicos
                'brand', 'model_family', 'description',
                
                // Contadores de páginas
                'oid_total_pages', 'oid_total_color_pages', 'oid_total_bw_pages', 'oid_total_copies',
                'oid_total_prints', 'oid_total_scans', 'oid_duplex_pages', 'oid_total_faxes',
                'oid_a4_pages', 'oid_a3_pages', 'oid_letter_pages', 'oid_legal_pages',
                
                // Tóner - niveles y capacidad
                'oid_black_toner_level', 'oid_cyan_toner_level', 'oid_magenta_toner_level', 'oid_yellow_toner_level',
                'oid_black_toner_max', 'oid_cyan_toner_max', 'oid_magenta_toner_max', 'oid_yellow_toner_max',
                'oid_black_toner_status', 'oid_cyan_toner_status', 'oid_magenta_toner_status', 'oid_yellow_toner_status',
                
                // Unidades de imagen / drums
                'oid_black_drum_level', 'oid_cyan_drum_level', 'oid_magenta_drum_level', 'oid_yellow_drum_level',
                
                // Otros consumibles
                'oid_fuser_unit_level', 'oid_transfer_belt_level', 'oid_waste_toner_level', 'oid_waste_toner_max',
                
                // Bandejas
                'oid_tray1_level', 'oid_tray1_max_capacity', 'oid_tray1_status', 'oid_tray1_paper_size', 'oid_tray1_paper_type',
                'oid_tray2_level', 'oid_tray2_max_capacity', 'oid_tray2_status', 'oid_tray2_paper_size', 'oid_tray2_paper_type',
                'oid_tray3_level', 'oid_tray3_max_capacity', 'oid_tray3_status', 'oid_tray3_paper_size', 'oid_tray3_paper_type',
                'oid_bypass_tray_level', 'oid_bypass_tray_status',
                
                // Sistema e información
                'oid_printer_status', 'oid_printer_model', 'oid_serial_number', 'oid_firmware_version',
                'oid_system_contact', 'oid_system_name', 'oid_system_location', 'oid_printer_memory',
                'oid_temperature', 'oid_display_message',
                
                // Mensajes y alertas
                'oid_error_messages', 'oid_warning_messages', 'oid_service_messages',
                
                // Red
                'oid_ip_address', 'oid_mac_address', 'oid_subnet_mask', 'oid_gateway'
            ];

            // Recopilar datos del formulario
            fields.forEach(field => {
                const value = getValue(field);
                if (value !== '') {  // Solo incluir campos con valor
                    formData[field] = value;
                }
            });

            const printerOidsId = form.dataset.printerOidsId;
            const url = printerOidsId ? `/printer-oids/${printerOidsId}/edit` : '/printer-oids/create';
            
            logDebug('URL de envío:', url);
            logDebug('Datos a enviar:', formData);

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            logDebug('Respuesta recibida:', {
                status: response.status,
                statusText: response.statusText
            });

            const contentType = response.headers.get("content-type");
            if (!contentType || !contentType.includes("application/json")) {
                throw new Error('Respuesta no válida del servidor');
            }

            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || 'Error al procesar el formulario');
            }

            showNotification(result.message || 'Configuración guardada exitosamente', 'success');

            // Redirigir después de un breve delay
            setTimeout(() => {
                window.location.href = result.redirect || '/printer-oids';
            }, 1500);

        } catch (error) {
            logDebug('Error en el proceso:', error);
            showNotification(error.message, 'error');
        }
    });

    // Función para limpiar formulario
    window.resetForm = function() {
        form.reset();
        showNotification('Formulario limpiado', 'info');
    };

    // Función para validar OID
    window.validateOID = function(input) {
        const oidPattern = /^([0-9]+\.)*[0-9]+$/;
        const value = input.value.trim();
        
        if (value && !oidPattern.test(value)) {
            input.classList.add('border-red-500');
            showNotification('Formato de OID inválido. Use formato numérico (ej: 1.3.6.1.2.1)', 'error');
        } else {
            input.classList.remove('border-red-500');
        }
    };
});

// Asegurarse de que existe el contenedor de notificaciones
document.addEventListener('DOMContentLoaded', function() {
    if (!document.getElementById('notification-container')) {
        const container = document.createElement('div');
        container.id = 'notification-container';
        document.body.appendChild(container);
    }
});