document.addEventListener('DOMContentLoaded', function() {
            // Manejar clic en iconos de PDF - Versión unificada
            document.querySelectorAll('.view-pdf').forEach(link => {
                link.addEventListener('click', async function(e) {
                    e.preventDefault();
                    const reqId = this.getAttribute('data-req-id');
                    const filePath = this.getAttribute('data-filepath');
                    
                    // Inicializar el modal correctamente
                    const pdfModal = new bootstrap.Modal(document.getElementById('pdfModal'));
                    
                    try {
                        // Mostrar el modal primero con un loader
                        document.getElementById('pdfViewer').src = '';
                        pdfModal.show();
                        
                        // Cargar el PDF
                        const response = await fetch(`/compras/ver-pdf/${reqId}/`);
                        
                        if (!response.ok) throw new Error('Error al cargar PDF');
                        
                        const blob = await response.blob();
                        const objectUrl = URL.createObjectURL(blob);
                        
                        // Configurar el visor
                        document.getElementById('pdfViewer').src = objectUrl;
                        document.getElementById('pdfDownloadBtn').href = objectUrl;
                        
                        // Manejar el cierre correctamente
                        const modalElement = document.getElementById('pdfModal');
                        const cleanUp = function() {
                            URL.revokeObjectURL(objectUrl);
                            modalElement.removeEventListener('hidden.bs.modal', cleanUp);
                        };
                        
                        modalElement.addEventListener('hidden.bs.modal', cleanUp);
                        
                    } catch (error) {
                        console.error('Error:', error);
                        pdfModal.hide();
                        
                        // Mostrar mensaje de error
                        const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
                        document.getElementById('errorMessage').textContent = 'No se pudo cargar el PDF';
                        errorModal.show();
                    }
                });
            });
        });