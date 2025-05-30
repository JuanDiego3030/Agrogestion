from django.contrib import messages
from compras.models import Requisicion, User_com
from requisitores.models import User_req  # Importa si es necesario
from datetime import datetime
from django.core.files.storage import default_storage
from directivos.models import User_dir

class RequisicionService:
    @staticmethod
    def crear_requisicion(request, user):
        try:
            codigo = request.POST.get('codigo', '').strip()
            fecha_requerida = request.POST.get('fecha_requerida', '')
            descripcion = request.POST.get('descripcion', '').strip()
            archivo = request.FILES.get('archivo')
            usuario_com_id = request.POST.get('usuario_com')
            archivo_aprobacion = request.FILES.get('archivo_aprobacion')
            importancia = request.POST.get('importancia', 'N')
            directivo_id = request.POST.get('directivo_id')

            # Validaciones básicas
            if not all([codigo, fecha_requerida, archivo, importancia, directivo_id]):
                messages.error(request, 'Todos los campos obligatorios deben estar completos')
                return False

            if Requisicion.objects.filter(codigo=codigo).exists():
                messages.error(request, 'El código ya existe')
                return False

            # Determinar usuario de compras asignado
            if usuario_com_id:
                usuario_com = User_com.objects.get(id=usuario_com_id)
            elif hasattr(user, 'user_com'):
                usuario_com = user  # Si es User_com, se asigna a sí mismo
            else:
                messages.error(request, 'Debe seleccionar un usuario de compras')
                return False

            # Obtener directivo
            try:
                directivo = User_dir.objects.get(id=directivo_id)
            except User_dir.DoesNotExist:
                messages.error(request, 'Directivo seleccionado no existe')
                return False

            requisicion = Requisicion(
                codigo=codigo,
                archivo=archivo,
                fecha_requerida=fecha_requerida,
                descripcion=descripcion,
                usuario=usuario_com,
                estado='P',
                importancia=importancia,
                directivo=directivo
            )

            # Si el usuario es User_req, guarda el nombre como creador
            if hasattr(user, 'nombre'):
                requisicion.creador_req = user.nombre

            # Manejar archivo de aprobación si se sube
            if archivo_aprobacion:
                if archivo_aprobacion.name.lower().endswith('.pdf') and archivo_aprobacion.size <= 5 * 1024 * 1024:
                    requisicion.archivo_aprobacion = archivo_aprobacion
                    requisicion.estado = 'A'
                else:
                    messages.error(request, 'El archivo de aprobación debe ser PDF y menor a 5MB')

            requisicion.save()
            messages.success(request, f'Requisición {codigo} creada exitosamente')
            return True

        except User_com.DoesNotExist:
            messages.error(request, 'Usuario de compras no válido')
            return False
        except Exception as e:
            messages.error(request, f'Error al crear requisición: {str(e)}')
            return False

    @staticmethod
    def editar_requisicion(request, user):
        req_id = request.POST.get('req_id')
        try:
            req = Requisicion.objects.get(id=req_id)

            # Permisos: User_com solo si es el asignado, User_req solo si es el creador
            if hasattr(user, 'nombre') and req.creador_req != user.nombre:
                messages.error(request, 'No tienes permiso para editar esta requisición')
                return False
            if hasattr(user, 'user_com') and req.usuario != user:
                messages.error(request, 'No tienes permiso para editar esta requisición')
                return False

            # Obtener datos del formulario
            codigo = request.POST.get('codigo', '').strip()
            fecha_requerida = request.POST.get('fecha_requerida')
            descripcion = request.POST.get('descripcion', '').strip()
            usuario_com_id = request.POST.get('usuario_com')
            importancia = request.POST.get('importancia', 'N')
            directivo_id = request.POST.get('directivo_id')

            # Validaciones
            if not codigo:
                messages.error(request, 'El código es obligatorio')
                return False
            if codigo != req.codigo and Requisicion.objects.filter(codigo=codigo).exists():
                messages.error(request, 'El código ya está en uso')
                return False

            # Actualizar usuario de compras si se envía
            if usuario_com_id:
                usuario_com = User_com.objects.get(id=usuario_com_id)
                req.usuario = usuario_com

            # Actualizar importancia
            if importancia in dict(Requisicion.IMPORTANCIA_CHOICES):
                req.importancia = importancia

            # Actualizar directivo
            if directivo_id:
                try:
                    directivo = User_dir.objects.get(id=directivo_id)
                    req.directivo = directivo
                except User_dir.DoesNotExist:
                    messages.error(request, 'Directivo seleccionado no existe')
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

            if 'archivo_aprobacion' in request.FILES:
                archivo_aprobacion = request.FILES['archivo_aprobacion']
                if archivo_aprobacion.name.lower().endswith('.pdf') and archivo_aprobacion.size <= 5 * 1024 * 1024:
                    if req.archivo_aprobacion:
                        req.archivo_aprobacion.delete()
                    req.archivo_aprobacion = archivo_aprobacion
                    req.estado = 'A'
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

            # Permisos: User_com solo si es el asignado, User_req solo si es el creador
            if hasattr(user, 'nombre') and req.creador_req != user.nombre:
                messages.error(request, 'No tienes permiso para eliminar esta requisición')
                return False
            if hasattr(user, 'user_com') and req.usuario != user:
                messages.error(request, 'No tienes permiso para eliminar esta requisición')
                return False

            codigo = req.codigo
            if req.archivo:
                try:
                    default_storage.delete(req.archivo.path)
                except Exception as e:
                    messages.error(request, f'Error al eliminar el archivo: {str(e)}')
                    return False

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
            if 'archivo_orden' not in request.FILES:
                messages.error(request, 'Debe adjuntar el archivo PDF de la orden')
                return False

            archivo = request.FILES['archivo_orden']
            OrdenCompraService.validar_archivo_pdf(archivo)

            archivo_aprobacion = None
            if 'archivo_aprobacion' in request.FILES:
                archivo_aprobacion = request.FILES['archivo_aprobacion']
                OrdenCompraService.validar_archivo_pdf(archivo_aprobacion)

            archivo_cuadro = None
            if 'archivo_cuadro_comparativo' in request.FILES:
                archivo_cuadro = request.FILES['archivo_cuadro_comparativo']
                OrdenCompraService.validar_archivo_pdf(archivo_cuadro)

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

            estado = 'A' if archivo_aprobacion else 'P'

            # Crear la orden de compra
            orden = OrdenCompra(
                codigo=datos['codigo'],
                archivo=archivo,
                archivo_aprobacion=archivo_aprobacion,
                archivo_cuadro_comparativo=archivo_cuadro,
                fecha_entrega_esperada=datos['fecha_entrega'],
                descripcion=datos['descripcion'],
                proveedor=f"{proveedor['codigo']} - {proveedor['nombre']}",
                requisicion=requisicion,
                creador=user,
                estado=estado
            )
            orden.full_clean()
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
            orden = OrdenCompra.objects.get(id=orden_id)

            # Verificar permisos
            if orden.creador != user:
                raise ValidationError('No tienes permiso para editar esta orden')

            # Obtener datos del formulario
            codigo = request.POST.get('codigo', '').strip()
            proveedor_info = request.POST.get('proveedor', '').strip()
            fecha_entrega = request.POST.get('fecha_entrega', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            estado = request.POST.get('estado', '').strip()

            # Solo validar código único si se modifica
            if codigo and codigo != orden.codigo:
                if OrdenCompra.objects.filter(codigo=codigo).exists():
                    raise ValidationError('El código ya está en uso')
                orden.codigo = codigo

            # Procesar proveedor solo si se envía uno nuevo
            if proveedor_info:
                proveedor = OrdenCompraService.obtener_proveedor_desde_formulario(proveedor_info)
                if not Proveedor.objects.using('sqlserver').filter(co_prov=proveedor['codigo']).exists():
                    raise ValidationError('El proveedor seleccionado no existe en el sistema')
                orden.proveedor = proveedor_info

            # Actualizar fecha de entrega si se envía
            if fecha_entrega:
                orden.fecha_entrega_esperada = fecha_entrega

            # Actualizar descripción si se envía
            if descripcion:
                orden.descripcion = descripcion

            # Actualizar estado si se envía
            if estado:
                orden.estado = estado

            # Manejo de archivos
            if 'archivo_orden' in request.FILES:
                archivo = request.FILES['archivo_orden']
                OrdenCompraService.validar_archivo_pdf(archivo)
                if orden.archivo:
                    orden.archivo.delete()
                orden.archivo = archivo

            if 'archivo_aprobacion' in request.FILES:
                archivo_aprobacion = request.FILES['archivo_aprobacion']
                OrdenCompraService.validar_archivo_pdf(archivo_aprobacion)
                if orden.archivo_aprobacion:
                    orden.archivo_aprobacion.delete()
                orden.archivo_aprobacion = archivo_aprobacion
                orden.estado = 'A'  # Solo aquí se cambia a aprobado

            if 'archivo_cuadro_comparativo' in request.FILES:
                archivo_cuadro = request.FILES['archivo_cuadro_comparativo']
                OrdenCompraService.validar_archivo_pdf(archivo_cuadro)
                if orden.archivo_cuadro_comparativo:
                    orden.archivo_cuadro_comparativo.delete()
                orden.archivo_cuadro_comparativo = archivo_cuadro

            orden.full_clean()
            orden.save()
            messages.success(request, f'Orden {orden.codigo} actualizada exitosamente!')
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