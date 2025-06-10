from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from compras.models import User_com
from requisitores.models import User_req
from directivos.models import User_dir
from gestion_admin.models import UserAdmin

def index(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        password = request.POST.get('password', '')

        # Admin
        try:
            user = UserAdmin.objects.get(nombre=nombre)
            if hasattr(user, 'bloqueado') and user.bloqueado:
                messages.error(request, 'Usuario bloqueado')
            elif check_password(password, user.password):
                request.session['user_admin_id'] = user.id
                return redirect('gestion_admin_usuarios')
            else:
                messages.error(request, 'Contraseña incorrecta')
            return render(request, 'index.html')
        except UserAdmin.DoesNotExist:
            pass

        # Directivo
        try:
            user = User_dir.objects.get(nombre=nombre)
            if hasattr(user, 'bloqueado') and user.bloqueado:
                messages.error(request, 'Usuario bloqueado')
            elif check_password(password, user.password):
                request.session['user_dir_id'] = user.id
                return redirect('directivos_requisiciones')
            else:
                messages.error(request, 'Contraseña incorrecta')
            return render(request, 'index.html')
        except User_dir.DoesNotExist:
            pass

        # Compras
        try:
            user = User_com.objects.get(nombre=nombre)
            if hasattr(user, 'bloqueado') and user.bloqueado:
                messages.error(request, 'Usuario bloqueado')
            elif check_password(password, user.password):
                request.session['user_com_id'] = user.id
                return redirect('compras_requisiciones')
            else:
                messages.error(request, 'Contraseña incorrecta')
            return render(request, 'index.html')
        except User_com.DoesNotExist:
            pass

        # Requisitor
        try:
            user = User_req.objects.get(nombre=nombre)
            if hasattr(user, 'bloqueado') and user.bloqueado:
                messages.error(request, 'Usuario bloqueado')
            elif check_password(password, user.password):
                request.session['user_req_id'] = user.id
                return redirect('requisitores_requisiciones')
            else:
                messages.error(request, 'Contraseña incorrecta')
            return render(request, 'index.html')
        except User_req.DoesNotExist:
            pass

        messages.error(request, 'Usuario no existe')
    return render(request, 'index.html')

def gestion_usuarios(request):
    if not request.session.get('user_admin_id'):
        return redirect('gestion_admin_login')

    tipo = request.GET.get('tipo', 'com')  # Por defecto muestra compras

    usuarios_com = User_com.objects.all() if tipo == 'com' else []
    usuarios_req = User_req.objects.all() if tipo == 'req' else []
    usuarios_dir = User_dir.objects.all() if tipo == 'dir' else []
    usuarios_admin = UserAdmin.objects.all() if tipo == 'admin' else []

    if request.method == 'POST':
        accion = request.POST.get('accion')
        tipo = request.POST.get('tipo')
        user_id = request.POST.get('user_id')
        nombre = request.POST.get('nombre')
        password = request.POST.get('password')
        firma = request.FILES.get('firma')  # <-- Nuevo: archivo de firma

        modelos = {
            'com': User_com,
            'req': User_req,
            'dir': User_dir,
            'admin': UserAdmin
        }
        Modelo = modelos.get(tipo)

        if accion == 'crear':
            if Modelo.objects.filter(nombre=nombre).exists():
                messages.error(request, 'El usuario ya existe')
            else:
                obj = Modelo(nombre=nombre)
                # Guardar correo electrónico
                email = request.POST.get('email')
                obj.email = email
                # Guardar tipo de compras si es usuario de compras
                if tipo == 'com':
                    tipo_compras = request.POST.get('tipo_compras', 'servicios')
                    obj.tipo_compras = tipo_compras
                    obj.is_master = request.POST.get('is_master') == 'on'
                # Guardar firma si es directivo
                if tipo == 'dir' and firma:
                    obj.firma = firma
                # Guardar contraseña encriptada
                if password:
                    obj.password = make_password(password)
                obj.save()
                messages.success(request, 'Usuario creado correctamente')
            return redirect('gestion_admin_usuarios')

        if accion == 'editar' and user_id:
            try:
                obj = Modelo.objects.get(id=user_id)
                obj.nombre = nombre
                # Actualizar correo electrónico
                email = request.POST.get('email')
                obj.email = email
                # Actualizar tipo de compras si es usuario de compras
                if tipo == 'com':
                    tipo_compras = request.POST.get('tipo_compras', 'servicios')
                    obj.tipo_compras = tipo_compras
                    obj.is_master = request.POST.get('is_master') == 'on'
                # Actualizar firma si es directivo y se sube nueva
                if tipo == 'dir' and firma:
                    obj.firma = firma
                # Actualizar contraseña encriptada si se proporciona
                if password:
                    obj.password = make_password(password)
                obj.bloqueado = 1 if request.POST.get('bloqueado') == 'on' else 0
                obj.save()
                messages.success(request, 'Usuario actualizado')
            except Modelo.DoesNotExist:
                messages.error(request, 'Usuario no encontrado')
            return redirect('gestion_admin_usuarios')

        if accion == 'bloquear' and user_id:
            try:
                obj = Modelo.objects.get(id=user_id)
                obj.bloqueado = not obj.bloqueado
                obj.save()
                messages.success(request, 'Usuario bloqueado/desbloqueado')
            except Modelo.DoesNotExist:
                messages.error(request, 'Usuario no encontrado')
            return redirect('gestion_admin_usuarios')

        if accion == 'eliminar' and user_id:
            try:
                obj = Modelo.objects.get(id=user_id)
                obj.delete()
                messages.success(request, 'Usuario eliminado')
            except Modelo.DoesNotExist:
                messages.error(request, 'Usuario no encontrado')
            return redirect('gestion_admin_usuarios')

    user_admin = UserAdmin.objects.get(id=request.session['user_admin_id'])
    return render(request, 'admin.html', {
        'user_admin': user_admin,
        'usuarios_com': usuarios_com,
        'usuarios_req': usuarios_req,
        'usuarios_dir': usuarios_dir,
        'usuarios_admin': usuarios_admin,
        'tipo': tipo,
    })

def logout(request):
    request.session.flush()  # Eliminar todas las sesiones
    return redirect('index')