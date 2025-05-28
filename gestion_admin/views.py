from django.shortcuts import render, redirect
from .models import UserAdmin
from compras.models import User_com
from requisitores.models import User_req
from directivos.models import User_dir
from django.contrib import messages

def index(request):
    return render(request, 'index.html')

def admin_login(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        password = request.POST.get('password', '')
        try:
            user = UserAdmin.objects.get(nombre=nombre)
            if user.bloqueado:
                messages.error(request, 'Usuario bloqueado')
            elif user.check_password(password):
                request.session['user_admin_id'] = user.id
                return redirect('gestion_admin_usuarios')
            else:
                messages.error(request, 'Contraseña incorrecta')
        except UserAdmin.DoesNotExist:
            messages.error(request, 'Usuario no existe')
    return render(request, 'admin_login.html')

def gestion_usuarios(request):
    if not request.session.get('user_admin_id'):
        return redirect('gestion_admin_login')

    # CRUD
    if request.method == 'POST':
        accion = request.POST.get('accion')
        tipo = request.POST.get('tipo')
        user_id = request.POST.get('user_id')
        nombre = request.POST.get('nombre')
        password = request.POST.get('password')

        # Selección de modelo según tipo
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
                if password:
                    if hasattr(obj, 'set_password'):
                        obj.set_password(password)
                    else:
                        obj.password = password
                obj.save()
                messages.success(request, 'Usuario creado correctamente')
            return redirect('gestion_admin_usuarios')

        if accion == 'editar' and user_id:
            try:
                obj = Modelo.objects.get(id=user_id)
                obj.nombre = nombre
                if password:
                    if hasattr(obj, 'set_password'):
                        obj.set_password(password)
                    else:
                        obj.password = password
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

    usuarios_com = User_com.objects.all()
    usuarios_req = User_req.objects.all()
    usuarios_dir = User_dir.objects.all()
    usuarios_admin = UserAdmin.objects.all()
    user_admin = UserAdmin.objects.get(id=request.session['user_admin_id'])
    return render(request, 'admin.html', {
        'usuarios_com': usuarios_com,
        'usuarios_req': usuarios_req,
        'usuarios_dir': usuarios_dir,
        'usuarios_admin': usuarios_admin,
        'user_admin': user_admin,
    })
