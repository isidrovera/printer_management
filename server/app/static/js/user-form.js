// static/js/user-form.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Inicializando formulario de usuario...');
    const form = document.getElementById('userForm');
    
    if (!form) {
        console.error('❌ No se encontró el formulario de usuario');
        return;
    }
    
    // Validación del formulario
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('📝 Iniciando envío del formulario...');
        
        if (!validateForm()) {
            console.warn('⚠️ Validación del formulario fallida');
            return;
        }
        
        const formData = new FormData(form);
        const userId = window.location.pathname.split('/').filter(Boolean).pop();
        const isEdit = window.location.pathname.includes('/edit');
        
        console.log('📊 Datos del formulario:', {
            isEdit,
            userId,
            formData: Object.fromEntries(formData)
        });
        
        try {
            console.log(`🔄 Enviando solicitud a ${isEdit ? '/users/${userId}/edit' : '/users/create'}`);
            const response = await fetch(isEdit ? `/users/${userId}/edit` : '/users/create', {
                method: 'POST',
                body: formData
            });
            
            console.log('📨 Respuesta recibida:', {
                status: response.status,
                ok: response.ok
            });
            
            const result = await response.json();
            console.log('📄 Datos de respuesta:', result);
            
            if (response.ok) {
                console.log('✅ Operación exitosa');
                showNotification(
                    isEdit ? 'Usuario actualizado exitosamente' : 'Usuario creado exitosamente',
                    'success'
                );
                setTimeout(() => window.location.href = '/users', 1000);
            } else {
                throw new Error(result.detail || 'Error procesando la solicitud');
            }
        } catch (error) {
            console.error('❌ Error:', error);
            showNotification(error.message, 'error');
        }
    });

    // Función de validación de contraseña
    function validatePassword(password) {
        console.log('🔒 Validando contraseña...');
        
        if (!password) {
            console.warn('⚠️ Contraseña vacía');
            return { isValid: false, errors: ['contraseña requerida'] };
        }

        const requirements = {
            hasUpperCase: /[A-Z]/.test(password),
            hasLowerCase: /[a-z]/.test(password),
            hasNumbers: /\d/.test(password),
            hasMinLength: password.length >= 8
        };

        console.log('📋 Requisitos de contraseña:', requirements);

        const errors = [];
        if (!requirements.hasUpperCase) errors.push('una letra mayúscula');
        if (!requirements.hasLowerCase) errors.push('una letra minúscula');
        if (!requirements.hasNumbers) errors.push('un número');
        if (!requirements.hasMinLength) errors.push('mínimo 8 caracteres');

        const isValid = Object.values(requirements).every(Boolean);
        console.log(`${isValid ? '✅' : '❌'} Validación de contraseña:`, { isValid, errors });

        return { isValid, errors };
    }
    
    // Validación del formulario
    function validateForm() {
        console.log('🔍 Iniciando validación del formulario...');
        
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            const value = field.value.trim();
            const isFieldValid = !!value;
            console.log(`📝 Campo ${field.name}:`, { 
                valor: value, 
                valido: isFieldValid 
            });

            if (!isFieldValid) {
                field.classList.add('border-red-500');
                isValid = false;
            } else {
                field.classList.remove('border-red-500');
            }
        });
        
        // Validación específica de la contraseña
        const passwordField = document.getElementById('password');
        if (passwordField) {
            const passwordValidation = validatePassword(passwordField.value);
            if (!passwordValidation.isValid) {
                passwordField.classList.add('border-red-500');
                showNotification(
                    `La contraseña debe contener: ${passwordValidation.errors.join(', ')}`, 
                    'error'
                );
                isValid = false;
            }
        }
        
        console.log(`${isValid ? '✅' : '❌'} Resultado de la validación:`, { isValid });
        return isValid;
    }
    
    // Validación en tiempo real del campo de contraseña
    const passwordField = document.getElementById('password');
    const passwordRequirements = document.getElementById('password-requirements');
    
    if (passwordField && passwordRequirements) {
        console.log('🔒 Configurando validación en tiempo real de contraseña');
        
        passwordField.addEventListener('input', function() {
            console.log('🔄 Actualizando requisitos de contraseña');
            const validationResult = validatePassword(this.value);
            
            if (this.value) {
                passwordRequirements.innerHTML = `
                    <div class="${validationResult.isValid ? 'text-green-600' : 'text-red-600'}">
                        Requisitos de contraseña:
                        <ul class="list-disc ml-4 mt-1">
                            ${validationResult.errors.map(error => `
                                <li>${error}</li>
                            `).join('')}
                        </ul>
                    </div>
                `;
            } else {
                passwordRequirements.innerHTML = '';
            }
        });
    }
    
    // Validación en tiempo real de campos requeridos
    const inputFields = form.querySelectorAll('input, select');
    inputFields.forEach(field => {
        field.addEventListener('input', function() {
            if (this.hasAttribute('required')) {
                if (!this.value.trim()) {
                    this.classList.add('border-red-500');
                } else {
                    this.classList.remove('border-red-500');
                }
            }
        });
    });
    
    // Función para mostrar notificaciones
    function showNotification(message, type = 'success') {
        console.log(`🔔 Mostrando notificación:`, { message, type });
        
        const container = document.getElementById('notification-container') || createNotificationContainer();
        const notification = document.createElement('div');
        
        notification.className = `p-4 rounded-lg shadow-lg ${
            type === 'success' ? 'bg-green-500' : 'bg-red-500'
        } text-white flex items-center justify-between mx-4`;
        
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} mr-2"></i>
                <span>${message}</span>
            </div>
            <button onclick="this.parentElement.remove()" class="ml-4">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        container.appendChild(notification);
        setTimeout(() => notification.remove(), 5000);
    }
    
    function createNotificationContainer() {
        console.log('📦 Creando contenedor de notificaciones');
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'fixed bottom-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
        return container;
    }
});