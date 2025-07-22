from compras.models import Requisicion, User_com, User_dir
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db import transaction
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.conf import settings
from requisitores.telegram_utils import send_telegram_message
import asyncio

class RequisicionService:
    @staticmethod
    @transaction.atomic
    def crear_requisicion(request, user):
        try:
            codigo = request.POST.get('codigo', '').strip()
            fecha_requerida = request.POST.get('fecha_requerida')
            descripcion = request.POST.get('descripcion', '').strip()
            usuario_com_id = request.POST.get('usuario_com')
            archivo = request.FILES.get('archivo')
            importancia = request.POST.get('importancia', 'N')
            directivo_id = request.POST.get('directivo_id')
            directivo = User_dir.objects.get(id=directivo_id) if directivo_id else None

            if not all([codigo, fecha_requerida, usuario_com_id, archivo]):
                messages.error(request, 'Todos los campos son obligatorios')
                return False

            if Requisicion.objects.filter(codigo=codigo).exists():
                messages.error(request, 'El código ya está en uso')
                return False

            usuario_com = User_com.objects.get(id=usuario_com_id)

            req = Requisicion(
                codigo=codigo,
                fecha_requerida=fecha_requerida,
                descripcion=descripcion,
                usuario=usuario_com,
                creador_req=user.nombre,
                archivo=archivo,
                importancia=importancia,
                directivo=directivo,
            )
            req.save()

            # Notificación por Telegram usando asyncio.run
            try:
                asyncio.run(send_telegram_message(
                    chat_id='@agrolucha',
                    message=f'Nueva requisición registrada:\nCódigo: {codigo}\nDescripción: {descripcion}\nFecha requerida: {fecha_requerida}\nImportancia: {importancia}'
                ))
            except Exception as e:
                messages.warning(request, f'No se pudo enviar la notificación de Telegram: {e}')

            # Enviar correo al comprador asignado
            try:
                send_mail(
                    subject=f'Nueva Requisición Asignada: {codigo}',
                    message=(
                        f'Hola {usuario_com.nombre},\n\n'
                        f'Se te ha asignado una nueva requisición.\n'
                        f'Código: {codigo}\n'
                        f'Descripción: {descripcion}\n'
                        f'Fecha requerida: {fecha_requerida}\n'
                        f'Importancia: {importancia}\n'
                        f'\nPor favor, ingresa al sistema para gestionarla.'
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[usuario_com.email],
                    fail_silently=False,
                )
            except Exception as e:
                messages.warning(request, f'La requisición fue creada pero no se pudo enviar el correo: {e}')

            messages.success(request, f'Requisición {codigo} creada exitosamente')
            return True

        except User_com.DoesNotExist:
            messages.error(request, 'Usuario de compras no válido')
            return False
        except Exception as e:
            messages.error(request, f'Error al crear requisición: {str(e)}')
            return False

    @staticmethod
    @transaction.atomic
    def editar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        
        try:
            req = Requisicion.objects.get(id=req_id)
            
            # Verificar permisos
            if req.creador_req != user.nombre:
                messages.error(request, 'No tienes permiso para editar esta requisición')
                return False
            
            # Obtener datos del formulario
            codigo = request.POST.get('codigo', '').strip()
            fecha_requerida = request.POST.get('fecha_requerida')
            descripcion = request.POST.get('descripcion', '').strip()
            importancia = request.POST.get('importancia', 'N')
            directivo_id = request.POST.get('directivo_id')
            directivo = User_dir.objects.get(id=directivo_id) if directivo_id else None
            
            # Validaciones
            if not codigo:
                messages.error(request, 'El código es obligatorio')
                return False
                
            if codigo != req.codigo and Requisicion.objects.filter(codigo=codigo).exists():
                messages.error(request, 'El código ya está en uso')
                return False
            
            # Manejo de archivos
            if 'archivo' in request.FILES:
                archivo = request.FILES['archivo']
                if archivo.name.lower().endswith('.pdf') and archivo.size <= 5 * 1024 * 1024:
                    if req.archivo:
                        req.archivo.delete()
                    req.archivo = archivo
                else:
                    messages.error(request, 'El archivo de requisición debe ser PDF y menor a 5MB')
            
            # Manejo de archivo de aprobación
            if 'archivo_aprobacion' in request.FILES:
                archivo_aprobacion = request.FILES['archivo_aprobacion']
                if archivo_aprobacion.name.lower().endswith('.pdf') and archivo_aprobacion.size <= 5 * 1024 * 1024:
                    if req.archivo_aprobacion:
                        req.archivo_aprobacion.delete()
                    req.archivo_aprobacion = archivo_aprobacion
                    req.estado = 'A'  # Cambiar a Aprobada
                else:
                    messages.error(request, 'El archivo de aprobación debe ser PDF y menor a 5MB')
            
            # Actualizar campos
            req.codigo = codigo
            req.fecha_requerida = fecha_requerida
            req.descripcion = descripcion
            req.importancia = importancia
            req.directivo = directivo
            req.save()
            
            messages.success(request, f'Requisición {codigo} actualizada exitosamente!')
            return True
            
        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada')
            return False
        except Exception as e:
            messages.error(request, f'Error al actualizar requisición: {str(e)}')
            return False
    
    @staticmethod
    @transaction.atomic
    def eliminar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        
        try:
            req = Requisicion.objects.get(id=req_id)
            
            # Verificar permisos (solo el dueño puede eliminar)
            if req.creador_req != user.nombre:
                messages.error(request, 'No tienes permiso para eliminar esta requisición')
                return False
                
            # Guardar código para el mensaje
            codigo = req.codigo
            
            # Eliminar el archivo físico primero
            if req.archivo:
                try:
                    default_storage.delete(req.archivo.path)
                except Exception as e:
                    messages.error(request, f'Error al eliminar el archivo: {str(e)}')
                    return False
            
            # Eliminar el registro de la base de datos
            req.delete()
            
            messages.success(request, f'Requisición {codigo} eliminada exitosamente!')
            return True
            
        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada')
            return False
        except Exception as e:
            messages.error(request, f'Error al eliminar requisición: {str(e)}')
            return False