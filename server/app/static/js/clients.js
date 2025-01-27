document.addEventListener('DOMContentLoaded', function() {
    // Inicializar iconos
    lucide.createIcons();

    // Elementos DOM
    const listViewBtn = document.getElementById('listViewBtn');
    const kanbanViewBtn = document.getElementById('kanbanViewBtn');
    const listView = document.getElementById('listView');
    const kanbanView = document.getElementById('kanbanView');

    // Cambiar a vista lista
    listViewBtn?.addEventListener('click', () => {
        listViewBtn.classList.add('active');
        kanbanViewBtn.classList.remove('active');
        listView.classList.remove('hidden');
        kanbanView.classList.add('hidden');
        localStorage.setItem('clientViewPreference', 'list');
    });

    // Cambiar a vista kanban
    kanbanViewBtn?.addEventListener('click', () => {
        kanbanViewBtn.classList.add('active');
        listViewBtn.classList.remove('active');
        kanbanView.classList.remove('hidden');
        listView.classList.add('hidden');
        localStorage.setItem('clientViewPreference', 'kanban');
    });

    // Restaurar preferencia guardada
    const savedView = localStorage.getItem('clientViewPreference');
    if (savedView === 'kanban') {
        kanbanViewBtn?.click();
    }
});

// Función para confirmar eliminación
function confirmDelete(clientId) {
    if (confirm('¿Estás seguro de que deseas eliminar este cliente?')) {
        // Aquí iría la lógica de eliminación
        console.log('Eliminando cliente:', clientId);
        
        // Ejemplo de petición DELETE
        fetch(`/clients/${clientId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => {
            if (response.ok) {
                // Eliminar elemento del DOM
                const elements = document.querySelectorAll(`[data-client-id="${clientId}"]`);
                elements.forEach(el => el.remove());
            } else {
                throw new Error('Error al eliminar');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al eliminar el cliente');
        });
    }
}