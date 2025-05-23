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
        
from django.db import transaction
from django.contrib import messages
from django.core.exceptions import ValidationError
from .models import OrdenCompra, Requisicion, Proveedor
from datetime import datetime
import os

class OrdenCompraService:
    
    @staticmethod
    def validar_archivo_pdf(archivo):
        """Valida que el archivo sea PDF y no exceda el tamaño máximo"""
        if not archivo.name.lower().endswith('.pdf'):
            raise ValidationError('El archivo de la orden debe ser PDF')
        if archivo.size > 5 * 1024 * 1024:  # 5MB
            raise ValidationError('El archivo no puede exceder los 5MB')
        return True

    @staticmethod
    def obtener_proveedor_desde_formulario(proveedor_info):
        """Procesa la información del proveedor del formulario"""
        if not proveedor_info:
            raise ValidationError('Debe seleccionar un proveedor')
            
        proveedor_parts = proveedor_info.split(' - ')
        if len(proveedor_parts) != 2:
            raise ValidationError('Formato de proveedor inválido')
            
        return {
            'codigo': proveedor_parts[0],
            'nombre': proveedor_parts[1]
        }

    @staticmethod
    @transaction.atomic
    def crear_orden(request, user):
        """
        Crea una nueva orden de compra con validación mejorada
        """
        try:
            # Validación de archivo
            if 'archivo_orden' not in request.FILES:
                raise ValidationError('Debe seleccionar un archivo PDF de la orden')
            
            archivo = request.FILES['archivo_orden']
            OrdenCompraService.validar_archivo_pdf(archivo)

            # Obtener y validar datos del formulario
            datos = {
                'codigo': request.POST.get('codigo_orden', '').strip(),
                'requisicion_id': request.POST.get('requisicion_id'),
                'proveedor_info': request.POST.get('proveedor', '').strip(),
                'fecha_entrega': request.POST.get('fecha_entrega', ''),
                'descripcion': request.POST.get('descripcion', '').strip(),
            }

            # Validar campos requeridos
            if not all(datos.values()):
                raise ValidationError('Todos los campos son obligatorios')
                
            # Validar código único
            if OrdenCompra.objects.filter(codigo=datos['codigo']).exists():
                raise ValidationError('El código de orden ya existe')

            # Obtener y validar requisición
            try:
                requisicion = Requisicion.objects.get(id=datos['requisicion_id'])
            except Requisicion.DoesNotExist:
                raise ValidationError('La requisición seleccionada no existe')

            # Procesar proveedor
            proveedor = OrdenCompraService.obtener_proveedor_desde_formulario(datos['proveedor_info'])
            
            # Verificar que el proveedor existe en la base de datos externa
            if not Proveedor.objects.using('sqlserver').filter(co_prov=proveedor['codigo']).exists():
                raise ValidationError('El proveedor seleccionado no existe en el sistema')

            # Crear la orden de compra
            orden = OrdenCompra(
                codigo=datos['codigo'],
                archivo=archivo,
                fecha_creacion=datetime.now(),
                fecha_entrega_esperada=datos['fecha_entrega'],
                descripcion=datos['descripcion'],
                proveedor=f"{proveedor['codigo']} - {proveedor['nombre']}",
                requisicion=requisicion,
                creador=user,
                estado='P'  # Por defecto Pendiente
            )

            orden.full_clean()  # Validación del modelo
            orden.save()
            
            messages.success(request, f'Orden de compra {datos["codigo"]} creada exitosamente!')
            return True
            
        except ValidationError as e:
            messages.error(request, str(e))
            return False
        except Exception as e:
            messages.error(request, f'Error inesperado al crear orden: {str(e)}')
            return False

    @staticmethod
    @transaction.atomic
    def editar_orden(request, user):
        """
        Edita una orden de compra existente con validación mejorada
        """
        try:
            orden_id = request.POST.get('orden_id')
            if not orden_id:
                raise ValidationError('ID de orden no proporcionado')
                
            orden = OrdenCompra.objects.select_for_update().get(id=orden_id)
            
            # Verificar permisos
            if orden.creador != user:
                raise ValidationError('No tienes permiso para editar esta orden')
            
            # Obtener datos del formulario
            datos = {
                'codigo': request.POST.get('codigo', '').strip(),
                'proveedor_info': request.POST.get('proveedor', '').strip(),
                'fecha_entrega': request.POST.get('fecha_entrega'),
                'descripcion': request.POST.get('descripcion', '').strip(),
                'estado': request.POST.get('estado', 'P'),
            }

            # Validar campos requeridos
            if not all([datos['codigo'], datos['proveedor_info'], datos['fecha_entrega']]):
                raise ValidationError('Todos los campos son obligatorios')
                
            # Validar código único (si cambió)
            if datos['codigo'] != orden.codigo and OrdenCompra.objects.filter(codigo=datos['codigo']).exists():
                raise ValidationError('El código ya está en uso')

            # Procesar proveedor
            proveedor = OrdenCompraService.obtener_proveedor_desde_formulario(datos['proveedor_info'])
            
            # Verificar que el proveedor existe en la base de datos externa
            if not Proveedor.objects.using('sqlserver').filter(co_prov=proveedor['codigo']).exists():
                raise ValidationError('El proveedor seleccionado no existe en el sistema')

            # Manejo de archivos
            if 'archivo_orden' in request.FILES:
                archivo = request.FILES['archivo_orden']
                OrdenCompraService.validar_archivo_pdf(archivo)
                
                # Eliminar archivo anterior si existe
                if orden.archivo:
                    try:
                        os.remove(orden.archivo.path)
                    except:
                        pass  # Si falla la eliminación del archivo físico, continuamos
                
                orden.archivo = archivo
            
            # Actualizar campos
            orden.codigo = datos['codigo']
            orden.proveedor = f"{proveedor['codigo']} - {proveedor['nombre']}"
            orden.fecha_entrega_esperada = datos['fecha_entrega']
            orden.descripcion = datos['descripcion']
            orden.estado = datos['estado']
            
            orden.full_clean()  # Validación del modelo
            orden.save()
            
            messages.success(request, f'Orden {datos["codigo"]} actualizada exitosamente!')
            return True
            
        except OrdenCompra.DoesNotExist:
            messages.error(request, 'Orden no encontrada')
            return False
        except ValidationError as e:
            messages.error(request, str(e))
            return False
        except Exception as e:
            messages.error(request, f'Error inesperado al actualizar orden: {str(e)}')
            return False

    @staticmethod
    @transaction.atomic
    def eliminar_orden(request, user):
        """
        Elimina una orden de compra con manejo seguro de transacciones
        """
        try:
            orden_id = request.POST.get('orden_id')
            if not orden_id:
                raise ValidationError('ID de orden no proporcionado')
                
            orden = OrdenCompra.objects.select_for_update().get(id=orden_id)
            
            # Verificar permisos
            if orden.creador != user:
                raise ValidationError('No tienes permiso para eliminar esta orden')
                
            # Guardar información para el mensaje
            codigo = orden.codigo
            archivo_path = orden.archivo.path if orden.archivo else None
            
            # Eliminar el registro
            orden.delete()
            
            # Eliminar archivo físico si existe
            if archivo_path and os.path.exists(archivo_path):
                try:
                    os.remove(archivo_path)
                except Exception as e:
                    print(f"Error al eliminar archivo físico: {str(e)}")
            
            messages.success(request, f'Orden {codigo} eliminada exitosamente!')
            return True
            
        except OrdenCompra.DoesNotExist:
            messages.error(request, 'Orden no encontrada')
            return False
        except ValidationError as e:
            messages.error(request, str(e))
            return False
        except Exception as e:
            messages.error(request, f'Error inesperado al eliminar orden: {str(e)}')
            return False

    @staticmethod
    def obtener_proveedores():
        """
        Obtiene la lista de proveedores desde la base de datos externa
        """
        try:
            return Proveedor.objects.using('sqlserver').all().order_by('prov_des')
        except Exception as e:
            print(f"Error al obtener proveedores: {str(e)}")
            return []