// static/js/printer-oids-form.js
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
            // Recopilar todos los campos del formulario
            const formData = {};
            const fields = [
                // Campos básicos
                'brand', 'model_family', 'description',
                
                // Contadores de páginas
                'oid_total_pages', 'oid_total_color_pages', 'oid_total_bw_pages', 'oid_total_copies',
                
                // Tóner
                'oid_black_toner_level', 'oid_cyan_toner_level', 'oid_magenta_toner_level', 'oid_yellow_toner_level',
                
                // Unidades de imagen
                'oid_black_drum_level', 'oid_cyan_drum_level', 'oid_magenta_drum_level', 'oid_yellow_drum_level',
                
                // Otros consumibles
                'oid_fuser_unit_level', 'oid_transfer_belt_level', 'oid_waste_toner_level', 'oid_waste_toner_max',
                
                // Bandejas (1,2,3)
                'oid_tray1_level', 'oid_tray1_max_capacity', 'oid_tray1_status', 'oid_tray1_paper_size', 'oid_tray1_paper_type',
                'oid_tray2_level', 'oid_tray2_max_capacity', 'oid_tray2_status', 'oid_tray2_paper_size', 'oid_tray2_paper_type',
                'oid_tray3_level', 'oid_tray3_max_capacity', 'oid_tray3_status', 'oid_tray3_paper_size', 'oid_tray3_paper_type',
                
                // Bandeja Bypass
                'oid_bypass_tray_level', 'oid_bypass_tray_status',
                
                // Sistema
                'oid_printer_status', 'oid_printer_model', 'oid_serial_number', 'oid_firmware_version',
                'oid_system_contact', 'oid_system_name'
            ];

            fields.forEach(field => {
                const value = getValue(field);
                formData[field] = value;
                logDebug(`Campo ${field}:`, value);
            });

            const printerOidsId = form.dataset.printerOidsId;
            const url = printerOidsId ? `/printer-oids/${printerOidsId}/edit` : '/printer-oids/create';
            
            logDebug('URL de envío:', url);
            logDebug('Datos a enviar:', formData);

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            logDebug('Respuesta recibida:', {
                status: response.status,
                statusText: response.statusText
            });

            if (response.redirected) {
                logDebug('Redirección detectada:', response.url);
                window.location.href = response.url;
                return;
            }

            if (!response.ok) {
                const contentType = response.headers.get("content-type");
                let errorMessage = 'Error al procesar el formulario';
                
                if (contentType && contentType.includes("application/json")) {
                    const errorData = await response.json();
                    logDebug('Error JSON recibido:', errorData);
                    errorMessage = errorData.detail || errorMessage;
                } else {
                    logDebug('Error no JSON recibido');
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            logDebug('Respuesta exitosa:', result);

            showNotification(
                `Configuración ${printerOidsId ? 'actualizada' : 'creada'} exitosamente`, 
                'success'
            );

            setTimeout(() => {
                window.location.href = '/printer-oids';
            }, 1500);

        } catch (error) {
            logDebug('Error en el proceso:', error);
            console.error('Error:', error);
            showNotification(error.message, 'error');
        }
    });
});

function getValue(id) {
    const element = document.getElementById(id);
    if (!element) {
        logDebug(`Campo no encontrado: ${id}`);
        return '';
    }
    return element.value.trim();
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