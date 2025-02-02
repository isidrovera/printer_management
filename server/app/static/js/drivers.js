document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    
    // Funcionalidad de búsqueda
    if (searchInput) {
        searchInput.addEventListener('input', function(e) {
            const searchTerm = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(searchTerm) ? '' : 'none';
            });
        });
    }
});

// Función para mostrar notificaciones
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500'
    };
    
    notification.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white ${colors[type]}`;
    notification.textContent = message;
    notification.classList.remove('hidden');
    
    // Animación de entrada
    notification.style.transform = 'translateY(0)';
    notification.style.opacity = '1';
    
    // Ocultar después de 3 segundos
    setTimeout(() => {
        notification.style.transform = 'translateY(100%)';
        notification.style.opacity = '0';
        setTimeout(() => {
            notification.classList.add('hidden');
        }, 300);
    }, 3000);
}

// Función para eliminar drivers
async function confirmDelete(id) {
    if (confirm('¿Estás seguro de que deseas eliminar este driver?')) {
        try {
            const response = await fetch(`/drivers/${id}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();

            if (data.success) {
                // Animación de eliminación
                const row = document.querySelector(`tr[data-driver-id="${id}"]`);
                if (row) {
                    row.style.backgroundColor = '#FEE2E2'; // Fondo rojo suave
                    row.style.transition = 'all 0.5s ease';
                    row.style.opacity = '0';
                    row.style.transform = 'translateX(100%)';
                    
                    setTimeout(() => {
                        row.remove();
                        showNotification('Driver eliminado con éxito', 'success');
                        
                        // Si no quedan más drivers, recargar para mostrar el mensaje de vacío
                        const remainingRows = document.querySelectorAll('tbody tr');
                        if (remainingRows.length === 0) {
                            location.reload();
                        }
                    }, 500);
                }
            } else {
                showNotification(data.error || 'Error al eliminar el driver', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Error al eliminar el driver', 'error');
        }
    }
}