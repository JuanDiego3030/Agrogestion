document.addEventListener('DOMContentLoaded', () => {
    // Configuración inicial - Cargar la sección guardada o la predeterminada
    const savedSection = localStorage.getItem('activeSection') || 'extensiones';
    loadSection(savedSection);
    setActiveNavItem(savedSection);
    
    setupNavigation();
    setupAlerts();
    setupFormSubmissions();
});

// Configuración de la navegación
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-links .nav-item');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const sectionName = link.getAttribute('data-section');
            switchSection(sectionName);
        });
    });
}

// Función para cambiar de sección
function switchSection(sectionName) {
    // Actualizar navegación
    setActiveNavItem(sectionName);
    
    // Cargar la sección
    loadSection(sectionName);
    
    // Guardar en localStorage
    localStorage.setItem('activeSection', sectionName);
}

// Establecer el ítem de navegación activo
function setActiveNavItem(sectionName) {
    const navLinks = document.querySelectorAll('.nav-links .nav-item');
    navLinks.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('data-section') === sectionName) {
            link.classList.add('active');
        }
    });
}

// Función para cargar secciones
function loadSection(sectionName) {
    const sections = document.querySelectorAll('#mainContent > div');
    sections.forEach(section => {
        section.style.display = 'none';
    });

    const activeSection = document.getElementById(sectionName);
    if (activeSection) {
        activeSection.style.display = 'block';
        
        // Desplazamiento suave al principio de la sección
        setTimeout(() => {
            activeSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }
}

// Configurar envío de formularios
function setupFormSubmissions() {
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function() {
            // Guardar la sección activa antes de enviar
            const activeSection = document.querySelector('.nav-links .nav-item.active');
            if (activeSection) {
                localStorage.setItem('activeSection', activeSection.getAttribute('data-section'));
            }
        });
    });
}

// Función para mostrar/ocultar formularios (sin cambios)
function toggleForm(formId) {
    const form = document.getElementById(formId);
    if (form.style.display === 'none' || form.style.display === '') {
        form.style.display = 'block';
        // Enfocar el primer campo del formulario
        const firstInput = form.querySelector('input, select, textarea');
        if (firstInput) {
            firstInput.focus();
        }
    } else {
        form.style.display = 'none';
    }
}

// Configuración de alertas (mejorada)
function setupAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Configurar temporizador para ocultar
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease-out';
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 3000);
        
        // Permitir cerrar manualmente
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '&times;';
        closeBtn.className = 'btn-close';
        closeBtn.style.position = 'absolute';
        closeBtn.style.right = '10px';
        closeBtn.style.top = '10px';
        closeBtn.addEventListener('click', () => alert.remove());
        alert.style.position = 'relative';
        alert.appendChild(closeBtn);
    });
}

// Función adicional para manejar modales
function setupModals() {
    document.querySelectorAll('[data-bs-toggle="modal"]').forEach(button => {
        button.addEventListener('click', function() {
            const targetModal = this.getAttribute('data-bs-target');
            const modal = document.querySelector(targetModal);
            if (modal) {
                // Guardar la sección activa al abrir modal
                const activeSection = document.querySelector('.nav-links .nav-item.active');
                if (activeSection) {
                    modal.dataset.activeSection = activeSection.getAttribute('data-section');
                }
            }
        });
    });
}