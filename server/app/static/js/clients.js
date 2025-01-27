document.addEventListener('DOMContentLoaded', function () {
    // Inicializar iconos de Lucide
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    } else {
        console.error('Lucide no está definido. Verifica que el script esté cargado correctamente.');
    }

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
        const deleteButton = document.querySelector(`button[data-client-id="${clientId}"]`);
        deleteButton.disabled = true;

        fetch(`/clients/${clientId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
        })
            .then((response) => {
                if (response.ok) {
                    document.querySelector(`[data-client-id="${clientId}"]`).remove();
                } else {
                    throw new Error('Error al eliminar el cliente');
                }
            })
            .catch((error) => {
                console.error('Error:', error);
                alert('Error al eliminar el cliente');
                deleteButton.disabled = false;
            });
    }
}
