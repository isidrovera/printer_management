// static/js/printer-oids-form.js
// static/js/printer-oids-form.js

document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!validateForm()) {
            showNotification('Por favor, complete los campos requeridos', 'error');
            return;
        }

        // Recopilar todos los campos del formulario
        const formData = {
            // Información Básica
            brand: getValue('brand'),
            model_family: getValue('model_family'),
            description: getValue('description'),
            
            // Contadores de Páginas
            oid_total_pages: getValue('oid_total_pages'),
            oid_total_color_pages: getValue('oid_total_color_pages'),
            oid_total_bw_pages: getValue('oid_total_bw_pages'),
            oid_total_copies: getValue('oid_total_copies'),
            
            // Tóner
            oid_black_toner_level: getValue('oid_black_toner_level'),
            oid_cyan_toner_level: getValue('oid_cyan_toner_level'),
            oid_magenta_toner_level: getValue('oid_magenta_toner_level'),
            oid_yellow_toner_level: getValue('oid_yellow_toner_level'),
            
            // Unidades de Imagen
            oid_black_drum_level: getValue('oid_black_drum_level'),
            oid_cyan_drum_level: getValue('oid_cyan_drum_level'),
            oid_magenta_drum_level: getValue('oid_magenta_drum_level'),
            oid_yellow_drum_level: getValue('oid_yellow_drum_level'),
            
            // Otros Consumibles
            oid_fuser_unit_level: getValue('oid_fuser_unit_level'),
            oid_transfer_belt_level: getValue('oid_transfer_belt_level'),
            oid_waste_toner_level: getValue('oid_waste_toner_level'),
            oid_waste_toner_max: getValue('oid_waste_toner_max'),
            
            // Bandejas
            // Bandeja 1
            oid_tray1_level: getValue('oid_tray1_level'),
            oid_tray1_max_capacity: getValue('oid_tray1_max_capacity'),
            oid_tray1_status: getValue('oid_tray1_status'),
            oid_tray1_paper_size: getValue('oid_tray1_paper_size'),
            oid_tray1_paper_type: getValue('oid_tray1_paper_type'),
            
            // Bandeja 2
            oid_tray2_level: getValue('oid_tray2_level'),
            oid_tray2_max_capacity: getValue('oid_tray2_max_capacity'),
            oid_tray2_status: getValue('oid_tray2_status'),
            oid_tray2_paper_size: getValue('oid_tray2_paper_size'),
            oid_tray2_paper_type: getValue('oid_tray2_paper_type'),
            
            // Bandeja 3
            oid_tray3_level: getValue('oid_tray3_level'),
            oid_tray3_max_capacity: getValue('oid_tray3_max_capacity'),
            oid_tray3_status: getValue('oid_tray3_status'),
            oid_tray3_paper_size: getValue('oid_tray3_paper_size'),
            oid_tray3_paper_type: getValue('oid_tray3_paper_type'),
            
            // Bandeja Bypass
            oid_bypass_tray_level: getValue('oid_bypass_tray_level'),
            oid_bypass_tray_status: getValue('oid_bypass_tray_status'),
            
            // Información del Sistema
            oid_printer_status: getValue('oid_printer_status'),
            oid_printer_model: getValue('oid_printer_model'),
            oid_serial_number: getValue('oid_serial_number'),
            oid_firmware_version: getValue('oid_firmware_version'),
            oid_system_contact: getValue('oid_system_contact'),
            oid_system_name: getValue('oid_system_name')
        };

        try {
            const printerOidsId = form.dataset.printerOidsId;
            const url = printerOidsId ? 
                `/printer-oids/${printerOidsId}/edit` : 
                '/printer-oids/create';

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(Object.fromEntries(new FormData(form)))
            });

            if (response.redirected) {
                window.location.href = response.url;
                return;
            }

            if (!response.ok) {
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.includes("application/json")) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || 'Error al procesar el formulario');
                }
                throw new Error('Error al procesar el formulario');
            }

            showNotification(
                `Configuración ${printerOidsId ? 'actualizada' : 'creada'} exitosamente`, 
                'success'
            );

            setTimeout(() => {
                window.location.href = '/printer-oids';
            }, 1500);

        } catch (error) {
            console.error('Error:', error);
            showNotification(error.message, 'error');
            
            // Actualizar mensaje de error en el formulario
            const errorDiv = document.querySelector('.error-message');
            if (errorDiv) {
                errorDiv.textContent = error.message;
                errorDiv.classList.remove('hidden');
            }
        }
    });
});

// Función de validación del formulario
function validateForm() {
    const requiredFields = ['brand', 'model_family'];
    let isValid = true;

    requiredFields.forEach(fieldId => {
        const field = document.getElementById(fieldId);
        if (field && !field.value.trim()) {
            isValid = false;
            field.classList.add('border-red-500');
        } else if (field) {
            field.classList.remove('border-red-500');
        }
    });

    return isValid;
}

// Función auxiliar para obtener el valor de un campo
function getValue(id) {
    const element = document.getElementById(id);
    return element ? element.value.trim() : '';
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    if (!container) return;

    const notification = document.createElement('div');
    notification.className = `flex items-center p-4 mb-4 rounded-lg shadow-lg ${
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
    
    const messageText = document.createElement('span');
    messageText.textContent = message;
    notification.appendChild(messageText);
    
    container.appendChild(notification);

    // Animación de entrada
    notification.style.opacity = '0';
    notification.style.transform = 'translateY(-20px)';
    notification.style.transition = 'all 0.3s ease-in-out';
    
    setTimeout(() => {
        notification.style.opacity = '1';
        notification.style.transform = 'translateY(0)';
    }, 10);

    // Animación de salida y eliminación
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateY(-20px)';
        
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 4700);
}

// Limpiar errores al escribir
document.addEventListener('input', function(e) {
    if (e.target.classList.contains('border-red-500')) {
        if (e.target.value.trim()) {
            e.target.classList.remove('border-red-500');
        }
    }
});