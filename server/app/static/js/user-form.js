// static/js/user-form.js

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('userForm');
    
    // Validación del formulario
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!validateForm()) {
            showNotification('Por favor, complete todos los campos requeridos.', 'error');
            return;
        }
        
        const formData = new FormData(form);
        const userId = window.location.pathname.split('/').filter(Boolean).pop();
        const isEdit = window.location.pathname.includes('/edit');
        
        try {
            const response = await fetch(isEdit ? `/users/${userId}/edit` : '/users/create', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (response.ok) {
                showNotification(
                    isEdit ? 'Usuario actualizado exitosamente' : 'Usuario creado exitosamente',
                    'success'
                );
                setTimeout(() => window.location.href = '/users', 1000);
            } else {
                throw new Error(result.detail || 'Error procesando la solicitud');
            }
        } catch (error) {
            showNotification(error.message, 'error');
        }
    });
    
    // Validación de campos
    function validateForm() {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('border-red-500');
                isValid = false;
            } else {
                field.classList.remove('border-red-500');
            }
        });
        
        // Validación específica de la contraseña en creación
        const passwordField = document.getElementById('password');
        if (passwordField && passwordField.value.length < 8) {
            passwordField.classList.add('border-red-500');
            isValid = false;
        }
        
        return isValid;
    }
    
    // Función para mostrar notificaciones
    function showNotification(message, type = 'success') {
        const container = document.getElementById('notification-container') || createNotificationContainer();
        const notification = document.createElement('div');
        
        notification.className = `p-4 rounded-lg shadow-lg ${
            type === 'success' ? 'bg-green-500' : 'bg-red-500'
        } text-white flex items-center justify-between`;
        
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
        const container = document.createElement('div');
        container.id = 'notification-container';
        container.className = 'fixed bottom-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
        return container;
    }
    
    // Validación en tiempo real
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
});