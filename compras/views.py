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


def compras_login(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()  # Limpiamos espacios en blanco
        password = request.POST.get('password', '')

        # Verificación básica de campos vacíos
        if not nombre or not password:
            messages.error(request, 'Por favor complete todos los campos')
            return redirect('compras_login')

        try:
            # Usamos get() con el nombre exacto (case sensitive)
            user_com = User_com.objects.get(nombre__exact=nombre)
            
            # Verificar si el usuario está bloqueado
            if user_com.bloqueado:
                messages.error(request, 'Este usuario está bloqueado. Contacte al administrador.')
                return redirect('compras_login')
            
            # Verificar la contraseña
            if check_password(password, user_com.password):
                request.session['user_com_id'] = user_com.id
                request.session['user_com_nombre'] = user_com.nombre
                return redirect('compras_requisiciones')  # Asegúrate que esta URL está definida
            else:
                messages.error(request, 'Contraseña incorrecta')
        except User_com.DoesNotExist:
            messages.error(request, 'Usuario no existe')
        except Exception as e:
            # Para propósitos de depuración durante desarrollo
            messages.error(request, f'Error en el sistema: {str(e)}')
    
    return render(request, 'compras_login.html')

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
    
    requisiciones = Requisicion.objects.all().order_by('-fecha_registro')

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
    
    ordenes_compra = OrdenCompra.objects.all().order_by('-fecha_creacion')
    requisiciones = Requisicion.objects.all().order_by('-fecha_registro')

    return render(request, 'ordenes.html', {
        'user': user,
        'ordenes_compra': OrdenCompra.objects.all().order_by('-fecha_creacion'),
        'requisiciones': Requisicion.objects.all().order_by('-fecha_registro'),
        'proveedores': proveedores,  # Pasar proveedores al template
        'estados_orden': OrdenCompra.ESTADOS,
        'fecha_minima': datetime.now().strftime('%Y-%m-%d')
    })

def ver_pdf(request, doc_type, doc_id):

    try:
        # Determinar el modelo y campo de archivo según el tipo
        if doc_type == 'requisicion':
            doc = get_object_or_404(Requisicion, id=doc_id)
            file_field = doc.archivo
            filename = f"requisicion_{doc.codigo}.pdf"
        elif doc_type == 'aprobacion':
            doc = get_object_or_404(Requisicion, id=doc_id)
            file_field = doc.archivo_aprobacion
            if not file_field:
                return HttpResponseNotFound("No existe archivo de aprobación")
            filename = f"aprobacion_{doc.codigo}.pdf"
        elif doc_type == 'orden':
            doc = get_object_or_404(OrdenCompra, id=doc_id)
            file_field = doc.archivo
            filename = f"orden_{doc.codigo}.pdf"
        else:
            return HttpResponseNotFound("Tipo de documento no válido")

        file_path = os.path.join(settings.MEDIA_ROOT, file_field.name)
        
        if not os.path.exists(file_path):
            return HttpResponseNotFound("El archivo no existe en el servidor")

        # Determinar si es para visualizar o descargar
        disposition = 'inline' if request.GET.get('view', 'true').lower() == 'true' else 'attachment'
        
        # Configurar la respuesta
        with open(file_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
            return response

    except Exception as e:
        return HttpResponseNotFound(f"Error al cargar el documento: {str(e)}")
    
def logout(request):
    request.session.flush()  # Eliminar todas las sesiones
    return redirect('compras_login')  # Redirigir a la página de inicio