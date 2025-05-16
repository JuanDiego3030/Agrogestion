from django.views.decorators.cache import never_cache
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import User_com, Requisicion, OrdenCompra
from django.shortcuts import get_object_or_404
from django.http import  Http404
import os
from django.http import FileResponse, Http404
from django.conf import settings
from .compras import RequisicionService, OrdenCompraService
from datetime import datetime

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
                return redirect('compras')  # Asegúrate que esta URL está definida
            else:
                messages.error(request, 'Contraseña incorrecta')
        except User_com.DoesNotExist:
            messages.error(request, 'Usuario no existe')
        except Exception as e:
            # Para propósitos de depuración durante desarrollo
            messages.error(request, f'Error en el sistema: {str(e)}')
    
    return render(request, 'compras_login.html')

@never_cache
def compras(request):
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
        
        # Manejo de requisiciones
        if accion == 'crear':
            if RequisicionService.crear_requisicion(request, user):
                return redirect('compras')
        
        elif accion == 'editar':
            if RequisicionService.editar_requisicion(request, user):
                return redirect('compras')
        
        elif accion == 'eliminar':
            if RequisicionService.eliminar_requisicion(request, user):
                return redirect('compras')
        
        # Manejo de órdenes de compra
        elif accion == 'crear_orden':
            if OrdenCompraService.crear_orden(request, user):
                return redirect('compras')
        
        elif accion == 'editar_orden':
            if OrdenCompraService.editar_orden(request, user):
                return redirect('compras')
        
        elif accion == 'eliminar_orden':
            if OrdenCompraService.eliminar_orden(request, user):
                return redirect('compras')
        
        return redirect('compras')
    
    # Obtener datos para ambas secciones
    requisiciones = Requisicion.objects.all().order_by('-fecha_registro')
    ordenes_compra = OrdenCompra.objects.all().order_by('-fecha_creacion')

    return render(request, 'compras.html', {
        'user': user,
        'requisiciones': requisiciones,
        'ordenes_compra': ordenes_compra,
        'estados': Requisicion.ESTADOS,
        'estados_orden': OrdenCompra.ESTADOS,
        'fecha_minima': datetime.now().strftime('%Y-%m-%d')
    })

def ver_pdf(request, req_id):
    req = get_object_or_404(Requisicion, id=req_id)
    file_path = os.path.join(settings.MEDIA_ROOT, req.archivo.name)
    
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    raise Http404("El archivo no existe")

def logout(request):
    request.session.flush()  # Eliminar todas las sesiones
    return redirect('compras_login')  # Redirigir a la página de inicio