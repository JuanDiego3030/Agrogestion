from django.views.decorators.cache import never_cache
from django.contrib.auth.hashers import check_password
from django.contrib import messages
from django.shortcuts import render, redirect
from .models import User_com, Requisicion
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
import os
from django.http import FileResponse, Http404
from django.conf import settings
import os

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
    
    # Manejar visualización de PDF
    if 'ver_pdf' in request.GET:
        req_id = request.GET.get('ver_pdf')
        try:
            req = Requisicion.objects.get(id=req_id, usuario=user)
            if not req.archivo.name.endswith('.pdf'):
                raise Http404("Solo se pueden visualizar archivos PDF")
            
            with open(req.archivo.path, 'rb') as fh:
                response = HttpResponse(fh.read(), content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="{os.path.basename(req.archivo.name)}"'
                return response
        except Requisicion.DoesNotExist:
            raise Http404("Requisición no encontrada")
    
    # Procesar acciones CRUD
    if request.method == 'POST':
        # Nueva requisición
        if 'archivo' in request.FILES:
            archivo = request.FILES['archivo']
            if not archivo.name.endswith('.pdf'):
                messages.error(request, 'Solo se aceptan archivos PDF')
            else:
                try:
                    # Crear la requisición (el código se genera automáticamente en save())
                    requisicion = Requisicion(
                        archivo=archivo,
                        usuario=user
                    )
                    requisicion.save()
                    messages.success(request, 'Requisición creada exitosamente!')
                except Exception as e:
                    messages.error(request, f'Error al crear requisición: {str(e)}')
            return redirect('compras')
        
        # Editar o eliminar
        req_id = request.POST.get('req_id')
        accion = request.POST.get('accion')
        
        try:
            req = Requisicion.objects.get(id=req_id, usuario=user)
            
            if accion == 'cambiar_estado':
                nuevo_estado = request.POST.get('nuevo_estado')
                if nuevo_estado in dict(Requisicion.ESTADOS):
                    req.estado = nuevo_estado
                    req.save()
                    messages.success(request, 'Estado actualizado!')
            
            elif accion == 'eliminar':
                req.delete()
                messages.success(request, 'Requisición eliminada!')
                
        except Requisicion.DoesNotExist:
            messages.error(request, 'Requisición no encontrada')
        except Exception as e:
            messages.error(request, f'Error al procesar la acción: {str(e)}')
        
        return redirect('compras')
    
    # Obtener requisiciones del usuario
    requisiciones = Requisicion.objects.filter(usuario=user).order_by('-fecha_registro')
    return render(request, 'compras.html', {
        'user': user,
        'requisiciones': requisiciones,
        'estados': Requisicion.ESTADOS
    })

def ver_pdf(request, req_id):
    req = get_object_or_404(Requisicion, id=req_id, usuario__id=request.session.get('user_com_id'))
    file_path = os.path.join(settings.MEDIA_ROOT, req.archivo.name)
    
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    raise Http404("El archivo no existe")

def logout(request):
    request.session.flush()  # Eliminar todas las sesiones
    return redirect('compras_login')  # Redirigir a la página de inicio