from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User_req
from compras.models import Requisicion, User_com, OrdenCompra
from compras.compras import RequisicionService
from django.views.decorators.cache import never_cache
from django.contrib.auth.hashers import check_password
from directivos.models import User_dir

def requisitores_login(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        password = request.POST.get('password', '')

        if not nombre or not password:
            messages.error(request, 'Por favor complete todos los campos')
            return redirect('requisitores_login')

        try:
            user_req = User_req.objects.get(nombre__exact=nombre)
            if user_req.bloqueado:
                messages.error(request, 'Este usuario está bloqueado.')
                return redirect('requisitores_login')
            if check_password(password, user_req.password):
                request.session['user_req_id'] = user_req.id
                request.session['user_req_nombre'] = user_req.nombre
                return redirect('requisitores_requisiciones')
            else:
                messages.error(request, 'Contraseña incorrecta')
        except User_req.DoesNotExist:
            messages.error(request, 'Usuario no existe')
    return render(request, 'requisitores_login.html')

@never_cache
def requisitores_requisiciones(request):
    user_id = request.session.get('user_req_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('requisitores_login')
    try:
        user = User_req.objects.get(id=user_id)
    except User_req.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('requisitores_login')

    # --- CRUD ---
    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'crear':
            if RequisicionService.crear_requisicion(request, user):
                messages.success(request, 'Requisición creada correctamente')
            else:
                messages.error(request, 'No se pudo crear la requisición')
            return redirect('requisitores_requisiciones')
        elif accion == 'editar':
            if RequisicionService.editar_requisicion(request, user):
                messages.success(request, 'Requisición editada correctamente')
            else:
                messages.error(request, 'No se pudo editar la requisición')
            return redirect('requisitores_requisiciones')
        elif accion == 'eliminar':
            if RequisicionService.eliminar_requisicion(request, user):
                messages.success(request, 'Requisición eliminada correctamente')
            else:
                messages.error(request, 'No se pudo eliminar la requisición')
            return redirect('requisitores_requisiciones')

    # Solo mostrar las requisiciones creadas por el requisitor logueado
    requisiciones = Requisicion.objects.filter(creador_req=user.nombre).order_by('-fecha_registro')

    buscar = request.GET.get('buscar', '').strip()
    estado = request.GET.get('estado', '').strip()

    if buscar:
        requisiciones = requisiciones.filter(codigo__icontains=buscar)
    if estado:
        requisiciones = requisiciones.filter(estado=estado)

    usuarios_compras = User_com.objects.all().order_by('nombre')
    directivos = User_dir.objects.all()

    requisiciones_ids = requisiciones.values_list('id', flat=True)
    ordenes = OrdenCompra.objects.filter(requisicion_id__in=requisiciones_ids).order_by('-fecha_creacion')

    return render(request, 'requisitores_requisiciones.html', {
        'user': user,
        'requisiciones': requisiciones,
        'usuarios_compras': usuarios_compras,
        'directivos': directivos,
        'ordenes': ordenes,
    })

def index(request):
    return render('index.html')

def logout(request):
    request.session.flush()  # Elimina todos los datos de la sesión
    messages.success(request, 'Has cerrado sesión exitosamente')
    return redirect('requisitores_login')