from django.contrib import messages
from django.shortcuts import redirect
from .models import Requisicion, OrdenCompra
from datetime import datetime
from django.core.files.storage import default_storage


class RequisicionService:
    @staticmethod
    def crear_requisicion(request, user):
        if 'archivo' not in request.FILES:
            messages.error(request, 'Debe seleccionar un archivo PDF de requisición')
            return False

        archivo = request.FILES['archivo']
        if not archivo.name.lower().endswith('.pdf'):
            messages.error(request, 'El archivo de requisición debe ser PDF')
            return False

        try:
            # Validaciones básicas
            if archivo.size > 5 * 1024 * 1024:
                messages.error(request, 'El archivo no puede exceder los 5MB')
                return False

            codigo = request.POST.get('codigo', '').strip()
            fecha_requerida = request.POST.get('fecha_requerida', '')
            descripcion = request.POST.get('descripcion', '').strip()
            
            if not codigo:
                messages.error(request, 'El código es obligatorio')
                return False
                
            if Requisicion.objects.filter(codigo=codigo).exists():
                messages.error(request, 'El código ya existe')
                return False

            # Crear la requisición
            requisicion = Requisicion(
                codigo=codigo,
                archivo=archivo,
                fecha_requerida=fecha_requerida,
                descripcion=descripcion,
                usuario=user,
                estado='P'  # Por defecto Pendiente
            )

            # Manejar archivo de aprobación si se sube
            if 'archivo_aprobacion' in request.FILES:
                archivo_aprobacion = request.FILES['archivo_aprobacion']
                if archivo_aprobacion.name.lower().endswith('.pdf'):
                    if archivo_aprobacion.size <= 5 * 1024 * 1024:
                        requisicion.archivo_aprobacion = archivo_aprobacion
                        requisicion.estado = 'A'  # Cambiar a Aprobada
                    else:
                        messages.error(request, 'El archivo de aprobación no puede exceder 5MB')
                else:
                    messages.error(request, 'El archivo de aprobación debe ser PDF')

            requisicion.save()
            messages.success(request, f'Requisición {codigo} creada exitosamente!')
            return True
            
        except Exception as e:
            messages.error(request, f'Error al crear requisición: {str(e)}')
            return False

    @staticmethod
    def editar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        
        try:
            req = Requisicion.objects.get(id=req_id)
            
            # Verificar permisos
            if req.usuario != user:
                messages.error(request, 'No tienes permiso para editar esta requisición')
                return False
            
            # Obtener datos del formulario
            codigo = request.POST.get('codigo', '').strip()
            fecha_requerida = request.POST.get('fecha_requerida')
            descripcion = request.POST.get('descripcion', '').strip()
            
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
    def eliminar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        
        try:
            req = Requisicion.objects.get(id=req_id)
            
            # Verificar permisos (solo el dueño puede eliminar)
            if req.usuario != user:
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
        
class OrdenCompraService:
    @staticmethod
    def crear_orden(request, user):
        if 'archivo_orden' not in request.FILES:
            messages.error(request, 'Debe seleccionar un archivo PDF de la orden')
            return False

        archivo = request.FILES['archivo_orden']
        if not archivo.name.lower().endswith('.pdf'):
            messages.error(request, 'El archivo de la orden debe ser PDF')
            return False

        try:
            # Validaciones básicas
            if archivo.size > 5 * 1024 * 1024:
                messages.error(request, 'El archivo no puede exceder los 5MB')
                return False

            codigo = request.POST.get('codigo_orden', '').strip()
            requisicion_id = request.POST.get('requisicion_id')
            proveedor = request.POST.get('proveedor', '').strip()
            fecha_entrega = request.POST.get('fecha_entrega', '')
            descripcion = request.POST.get('descripcion', '').strip()
            
            # Validaciones de campos requeridos
            if not all([codigo, requisicion_id, proveedor, fecha_entrega]):
                messages.error(request, 'Todos los campos son obligatorios')
                return False
                
            if OrdenCompra.objects.filter(codigo=codigo).exists():
                messages.error(request, 'El código de orden ya existe')
                return False

            # Verificar que la requisición existe
            try:
                requisicion = Requisicion.objects.get(id=requisicion_id)
            except Requisicion.DoesNotExist:
                messages.error(request, 'La requisición seleccionada no existe')
                return False

            # Crear la orden de compra
            orden = OrdenCompra(
                codigo=codigo,
                archivo=archivo,
                fecha_entrega_esperada=fecha_entrega,
                descripcion=descripcion,
                proveedor=proveedor,
                requisicion=requisicion,
                creador=user,
                estado='P'  # Por defecto Pendiente
            )

            orden.save()
            messages.success(request, f'Orden de compra {codigo} creada exitosamente!')
            return True
            
        except Exception as e:
            messages.error(request, f'Error al crear orden de compra: {str(e)}')
            return False

    @staticmethod
    def editar_orden(request, user):
        orden_id = request.POST.get('orden_id')
        
        try:
            orden = OrdenCompra.objects.get(id=orden_id)
            
            # Verificar permisos
            if orden.creador != user:
                messages.error(request, 'No tienes permiso para editar esta orden')
                return False
            
            # Obtener datos del formulario
            codigo = request.POST.get('codigo', '').strip()
            proveedor = request.POST.get('proveedor', '').strip()
            fecha_entrega = request.POST.get('fecha_entrega')
            descripcion = request.POST.get('descripcion', '').strip()
            estado = request.POST.get('estado', 'P')
            
            # Validaciones
            if not all([codigo, proveedor, fecha_entrega]):
                messages.error(request, 'Todos los campos son obligatorios')
                return False
                
            if codigo != orden.codigo and OrdenCompra.objects.filter(codigo=codigo).exists():
                messages.error(request, 'El código ya está en uso')
                return False
            
            # Manejo de archivos
            if 'archivo_orden' in request.FILES:
                archivo = request.FILES['archivo_orden']
                if archivo.name.lower().endswith('.pdf') and archivo.size <= 5 * 1024 * 1024:
                    if orden.archivo:
                        orden.archivo.delete()
                    orden.archivo = archivo
                else:
                    messages.error(request, 'El archivo de orden debe ser PDF y menor a 5MB')
            
            # Actualizar campos
            orden.codigo = codigo
            orden.proveedor = proveedor
            orden.fecha_entrega_esperada = fecha_entrega
            orden.descripcion = descripcion
            orden.estado = estado
            orden.save()
            
            messages.success(request, f'Orden {codigo} actualizada exitosamente!')
            return True
            
        except OrdenCompra.DoesNotExist:
            messages.error(request, 'Orden no encontrada')
            return False
        except Exception as e:
            messages.error(request, f'Error al actualizar orden: {str(e)}')
            return False
    
    @staticmethod
    def eliminar_orden(request, user):
        orden_id = request.POST.get('orden_id')
        
        try:
            orden = OrdenCompra.objects.get(id=orden_id)
            
            # Verificar permisos (solo el creador puede eliminar)
            if orden.creador != user:
                messages.error(request, 'No tienes permiso para eliminar esta orden')
                return False
                
            # Guardar código para el mensaje
            codigo = orden.codigo
            
            # Eliminar el registro (el modelo ya maneja la eliminación del archivo)
            orden.delete()
            
            messages.success(request, f'Orden {codigo} eliminada exitosamente!')
            return True
            
        except OrdenCompra.DoesNotExist:
            messages.error(request, 'Orden no encontrada')
            return False
        except Exception as e:
            messages.error(request, f'Error al eliminar orden: {str(e)}')
            return False