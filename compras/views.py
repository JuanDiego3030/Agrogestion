from django.views.decorators.cache import never_cache
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import User_com, Requisicion, OrdenCompra, Proveedor
from django.shortcuts import get_object_or_404
import os
from django.http import FileResponse, HttpResponseNotFound
from django.conf import settings
from .compras import RequisicionService, OrdenCompraService
from datetime import datetime
from django.urls import reverse
from django.http import FileResponse, HttpResponse
from django.conf import settings
import os
import tempfile
import shutil
import zipfile
from django.http import FileResponse, HttpResponseBadRequest
from django.utils.text import slugify


@never_cache
def compras_requisiciones(request):
    # Verificar sesión
    user_id = request.session.get('user_com_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('compras_login')
    
    try:
        user = User_com.objects.get(id=user_id)
    except User_com.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('compras_login')
        
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'crear':
            if RequisicionService.crear_requisicion(request, user):
                return redirect('compras_requisiciones')
        elif accion == 'editar':
            if RequisicionService.editar_requisicion(request, user):
                return redirect('compras_requisiciones')
        elif accion == 'eliminar':
            if RequisicionService.eliminar_requisicion(request, user):
                return redirect('compras_requisiciones')
        return redirect('compras_requisiciones')

    if user.is_master:
        requisiciones = Requisicion.objects.all()
    else:
        requisiciones = Requisicion.objects.filter(usuario=user)

    buscar = request.GET.get('buscar', '').strip()
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    estado = request.GET.get('estado', '').strip()

    requisiciones = Requisicion.objects.all()

    if buscar:
        requisiciones = requisiciones.filter(codigo__icontains=buscar)
    if fecha_desde:
        requisiciones = requisiciones.filter(fecha_registro__date__gte=fecha_desde)
    if fecha_hasta:
        requisiciones = requisiciones.filter(fecha_registro__date__lte=fecha_hasta)
    if estado:
       requisiciones = requisiciones.filter(estado=estado)

    return render(request, 'requisiciones.html', {
        'user': user,
        'requisiciones': requisiciones,
        'fecha_minima': datetime.now().strftime('%Y-%m-%d')
    })

@never_cache
def compras_ordenes(request):
    # Verificar sesión
    user_id = request.session.get('user_com_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('compras_login')
    
    try:
        user = User_com.objects.get(id=user_id)
    except User_com.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('compras_login')
    
    # Obtener proveedores de la base de datos SQL Server
    try:
        proveedores = Proveedor.objects.using('sqlserver').all().order_by('prov_des')
    except Exception as e:
        messages.error(request, f'Error al cargar proveedores: {str(e)}')
        proveedores = []
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'crear_orden':
            if OrdenCompraService.crear_orden(request, user):
                return redirect('compras_ordenes')
        
    if request.method == 'POST':
        accion = request.POST.get('accion')
        
        if accion == 'crear_orden':
            if OrdenCompraService.crear_orden(request, user):
                return redirect('compras_ordenes')
        
        elif accion == 'editar_orden':
            if OrdenCompraService.editar_orden(request, user):
                return redirect('compras_ordenes')
        
        elif accion == 'eliminar_orden':
            if OrdenCompraService.eliminar_orden(request, user):
                return redirect('compras_ordenes')
        
        return redirect('compras_ordenes')
    
    # Ejemplo para mostrar todas las órdenes y requisiciones si es master
    if user.is_master:
        ordenes_compra = OrdenCompra.objects.all()
        requisiciones = Requisicion.objects.all()
    else:
        ordenes_compra = OrdenCompra.objects.filter(requisicion__usuario=user)
        requisiciones = Requisicion.objects.filter(usuario=user)

    buscar = request.GET.get('buscar', '').strip()
    estado = request.GET.get('estado', '').strip()
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    proveedor = request.GET.get('proveedor', '').strip()

    if buscar:
        ordenes_compra = ordenes_compra.filter(codigo__icontains=buscar)
    if estado:
        ordenes_compra = ordenes_compra.filter(estado=estado)
    if fecha_desde:
        ordenes_compra = ordenes_compra.filter(fecha_creacion__date__gte=fecha_desde)
    if fecha_hasta:
        ordenes_compra = ordenes_compra.filter(fecha_creacion__date__lte=fecha_hasta)
    if proveedor:
        ordenes_compra = ordenes_compra.filter(proveedor__icontains=proveedor)

    return render(request, 'ordenes.html', {
        'user': user,
        'ordenes_compra': ordenes_compra,
        'requisiciones': requisiciones,
        'proveedores': proveedores,  # Pasar proveedores al template
        'estados_orden': OrdenCompra.ESTADOS,
        'fecha_minima': datetime.now().strftime('%Y-%m-%d')
    })

def ver_pdf(request, doc_type, doc_id):
    import os
    try:
        if doc_type == 'orden':
            doc = get_object_or_404(OrdenCompra, id=doc_id)
            file_field = doc.archivo
            filename = f"orden_{doc.codigo}.pdf"
        elif doc_type == 'orden_aprobacion':
            doc = get_object_or_404(OrdenCompra, id=doc_id)
            file_field = doc.archivo_aprobacion
            if not file_field:
                return HttpResponseNotFound("No existe archivo de aprobación")
            filename = f"aprobacion_orden_{doc.codigo}.pdf"
        elif doc_type == 'cuadro_comparativo':
            doc = get_object_or_404(OrdenCompra, id=doc_id)
            file_field = doc.archivo_cuadro_comparativo
            if not file_field:
                return HttpResponseNotFound("No existe archivo de cuadro comparativo")
            filename = f"cuadro_comparativo_{doc.codigo}.pdf"
        elif doc_type == 'requisicion':
            doc = get_object_or_404(Requisicion, id=doc_id)
            file_field = doc.archivo
            filename = f"requisicion_{doc.codigo}.pdf"
        elif doc_type == 'aprobacion':
            doc = get_object_or_404(Requisicion, id=doc_id)
            file_field = doc.archivo_aprobacion
            if not file_field:
                return HttpResponseNotFound("No existe archivo de aprobación")
            filename = f"aprobacion_{doc.codigo}.pdf"
        else:
            return HttpResponseNotFound("Tipo de documento no válido")

        file_path = os.path.join(settings.MEDIA_ROOT, file_field.name)
        
        if not os.path.exists(file_path):
            return HttpResponseNotFound("El archivo no existe en el servidor")

        disposition = 'inline' if request.GET.get('view', 'true').lower() == 'true' else 'attachment'
        with open(file_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
            return response

    except Exception as e:
        return HttpResponseNotFound(f"Error al cargar el documento: {str(e)}")
    
def logout(request):
    request.session.flush()  # Eliminar todas las sesiones
    return redirect('index')  # Redirigir a la página de inicio

def exportar_archivos(request):
    if request.method == 'POST':
        fecha_desde = request.POST.get('fecha_desde')
        fecha_hasta = request.POST.get('fecha_hasta')
        if not fecha_desde or not fecha_hasta:
            return HttpResponseBadRequest("Debe seleccionar ambas fechas.")

        # Filtrar órdenes y requisiciones por fecha
        ordenes = OrdenCompra.objects.filter(fecha_creacion__date__gte=fecha_desde, fecha_creacion__date__lte=fecha_hasta)
        requisiciones = Requisicion.objects.filter(fecha_registro__date__gte=fecha_desde, fecha_registro__date__lte=fecha_hasta)

        # Crear carpeta temporal
        temp_dir = tempfile.mkdtemp()
        try:
            # Guardar archivos de órdenes
            for orden in ordenes:
                carpeta = os.path.join(temp_dir, f"OC_{slugify(orden.codigo)}_{orden.fecha_creacion.strftime('%Y%m%d')}")
                os.makedirs(carpeta, exist_ok=True)
                if orden.archivo:
                    shutil.copy(orden.archivo.path, os.path.join(carpeta, os.path.basename(orden.archivo.name)))
                if hasattr(orden, 'archivo_aprobacion') and orden.archivo_aprobacion:
                    shutil.copy(orden.archivo_aprobacion.path, os.path.join(carpeta, os.path.basename(orden.archivo_aprobacion.name)))
                if hasattr(orden, 'archivo_cuadro_comparativo') and orden.archivo_cuadro_comparativo:
                    shutil.copy(orden.archivo_cuadro_comparativo.path, os.path.join(carpeta, os.path.basename(orden.archivo_cuadro_comparativo.name)))
            # Guardar archivos de requisiciones
            for req in requisiciones:
                carpeta = os.path.join(temp_dir, f"REQ_{slugify(req.codigo)}_{req.fecha_registro.strftime('%Y%m%d')}")
                os.makedirs(carpeta, exist_ok=True)
                if req.archivo:
                    shutil.copy(req.archivo.path, os.path.join(carpeta, os.path.basename(req.archivo.name)))
                if hasattr(req, 'archivo_aprobacion') and req.archivo_aprobacion:
                    shutil.copy(req.archivo_aprobacion.path, os.path.join(carpeta, os.path.basename(req.archivo_aprobacion.name)))

            # Crear archivo .zip
            zip_path = os.path.join(temp_dir, f"exportacion_{fecha_desde}_a_{fecha_hasta}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file.endswith('.zip'):
                            continue
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
            # Descargar el .zip
            response = FileResponse(open(zip_path, 'rb'), as_attachment=True, filename=os.path.basename(zip_path))
            return response
        finally:
            shutil.rmtree(temp_dir)
    else:
        return HttpResponseBadRequest("Método no permitido.")