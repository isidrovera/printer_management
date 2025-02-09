document.addEventListener('DOMContentLoaded', function() {
    // Animación de entrada para las tarjetas
    const cards = document.querySelectorAll('.card');
    
    function showCards() {
        cards.forEach((card, index) => {
            setTimeout(() => {
                card.style.animation = `fadeInUp 0.5s ease ${index * 0.1}s forwards`;
                card.classList.add('show');
            }, index * 100);
        });
    }

    // Iniciar animaciones al cargar
    showCards();

    // Animación del icono de configuración
    const cogIcon = document.querySelector('.fa-cog');
    if (cogIcon) {
        let rotation = 0;
        setInterval(() => {
            rotation += 360;
            cogIcon.style.transform = `rotate(${rotation}deg)`;
            cogIcon.style.transition = 'transform 2s ease';
        }, 3000);
    }

    // Animación de la campana
    const bellIcon = document.querySelector('.fa-bell');
    if (bellIcon) {
        setInterval(() => {
            bellIcon.style.animation = 'ringBell 0.5s ease';
            setTimeout(() => {
                bellIcon.style.animation = 'none';
            }, 500);
        }, 5000);
    }

    // Efecto hover para iconos en las tarjetas
    const cardIcons = document.querySelectorAll('.icon-circle i');
    cardIcons.forEach(icon => {
        icon.addEventListener('mouseover', function() {
            this.style.transform = 'scale(1.2) rotate(5deg)';
        });

        icon.addEventListener('mouseout', function() {
            this.style.transform = 'scale(1)';
        });
    });

    // Efecto ripple para los enlaces
    const cardLinks = document.querySelectorAll('.card-link');
    cardLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const ripple = document.createElement('div');
            ripple.classList.add('ripple');
            
            const rect = link.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            link.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
    });

    // Observador de intersección para animaciones al hacer scroll
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('show');
            }
        });
    }, {
        threshold: 0.1
    });

    cards.forEach(card => {
        observer.observe(card);
    });

    // Función para cargar y actualizar estadísticas
    async function loadDashboardStats() {
        try {
            const response = await fetch('/api/v1/dashboard/stats');
            const data = await response.json();
            
            // Actualizar contadores
            updateCounter('total-clients', data.clients?.total || 0);
            updateCounter('total-agents', data.agents?.total || 0);
            updateCounter('online-agents', data.agents?.online || 0);
            updateCounter('total-printers', data.printers?.total || 0);
            updateCounter('total-tunnels', data.tunnels?.total || 0);
            
        } catch (error) {
            console.error('Error al cargar estadísticas:', error);
        }
    }

    // Función para animar contadores
    function updateCounter(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            const startValue = parseInt(element.textContent) || 0;
            const increment = (value - startValue) / 20;
            let currentValue = startValue;

            const animation = setInterval(() => {
                currentValue += increment;
                if (
                    (increment > 0 && currentValue >= value) || 
                    (increment < 0 && currentValue <= value)
                ) {
                    element.textContent = value;
                    clearInterval(animation);
                } else {
                    element.textContent = Math.round(currentValue);
                }
            }, 50);
        }
    }

    // Cargar estadísticas iniciales y configurar actualización automática
    loadDashboardStats();
    setInterval(loadDashboardStats, 30000); // Actualizar cada 30 segundos

    // Event listeners para elementos interactivos
    document.querySelectorAll('.nav-icons i').forEach(icon => {
        icon.addEventListener('click', function() {
            this.classList.add('clicked');
            setTimeout(() => {
                this.classList.remove('clicked');
            }, 200);
        });
    });
});