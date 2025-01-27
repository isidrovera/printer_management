document.addEventListener('DOMContentLoaded', function() {
    // Inicializar iconos
    lucide.createIcons();

    // Toggle de vistas
    const listViewBtn = document.getElementById('listViewBtn');
    const kanbanViewBtn = document.getElementById('kanbanViewBtn');
    
    if (listViewBtn && kanbanViewBtn) {
        listViewBtn.addEventListener('click', () => {
            listViewBtn.classList.add('active');
            kanbanViewBtn.classList.remove('active');
        });

        kanbanViewBtn.addEventListener('click', () => {
            kanbanViewBtn.classList.add('active');
            listViewBtn.classList.remove('active');
        });
    }

    // Configurar acciones de eliminar
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', () => {
            const clientId = button.closest('tr').querySelector('td').textContent;
            if (confirm('¿Estás seguro de que deseas eliminar este cliente?')) {
                console.log(`Eliminando cliente ${clientId}`);
            }
        });
    });
});