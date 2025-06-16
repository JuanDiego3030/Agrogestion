from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User_req
from compras.models import Requisicion, User_com, OrdenCompra
from compras.compras import RequisicionService
from django.views.decorators.cache import never_cache
from django.contrib.auth.hashers import check_password
from directivos.models import User_dir
from django.core.mail import send_mail
from django.conf import settings

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
        return redirect('requisitores_login')
    try:
        user = User_req.objects.get(id=user_id)
    except User_req.DoesNotExist:
        return redirect('requisitores_login')


    if request.method == 'POST':
        accion = request.POST.get('accion')
        if accion == 'crear':
            exito = RequisicionService.crear_requisicion(request, user)
            if exito:
                usuario_com_id = request.POST.get('usuario_com')
                codigo = request.POST.get('codigo', '').strip()
                descripcion = request.POST.get('descripcion', '').strip()
                fecha_requerida = request.POST.get('fecha_requerida')
                importancia = request.POST.get('importancia', 'N')
                directivo_id = request.POST.get('directivo_id')
                try:
                    usuario_com = User_com.objects.get(id=usuario_com_id)
                    if usuario_com.email:
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
                    # Enviar correo al directivo si existe y tiene email
                    if directivo_id:
                        try:
                            directivo = User_dir.objects.get(id=directivo_id)
                            if directivo.email:
                                send_mail(
                                    subject=f'Nueva Requisición para su aprobación: {codigo}',
                                    message=(
                                        f'Hola {directivo.nombre},\n\n'
                                        f'Se ha creado una nueva requisición que requiere su aprobación.\n'
                                        f'Código: {codigo}\n'
                                        f'Descripción: {descripcion}\n'
                                        f'Fecha requerida: {fecha_requerida}\n'
                                        f'Importancia: {importancia}\n'
                                        f'\nPor favor, ingrese al sistema para revisarla.'
                                    ),
                                    from_email=settings.EMAIL_HOST_USER,
                                    recipient_list=[directivo.email],
                                    fail_silently=False,
                                )
                        except User_dir.DoesNotExist:
                            pass
                except Exception:
                    pass
            return redirect('requisitores_requisiciones')
        elif accion == 'editar':
            RequisicionService.editar_requisicion(request, user)
            return redirect('requisitores_requisiciones')
        elif accion == 'eliminar':
            RequisicionService.eliminar_requisicion(request, user)
            return redirect('requisitores_requisiciones')

    buscar = request.GET.get('buscar', '').strip()
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    estado = request.GET.get('estado', '').strip()

    # Solo requisiciones creadas por el usuario actual
    requisiciones = Requisicion.objects.filter(creador_req=user.nombre)

    if buscar:
        requisiciones = requisiciones.filter(codigo__icontains=buscar)
    if fecha_desde:
        requisiciones = requisiciones.filter(fecha_registro__date__gte=fecha_desde)
    if fecha_hasta:
        requisiciones = requisiciones.filter(fecha_registro__date__lte=fecha_hasta)
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
    return render(request, 'index.html')

def logout(request):
    request.session.flush()  # Eliminar todas las sesiones
    return redirect('index')