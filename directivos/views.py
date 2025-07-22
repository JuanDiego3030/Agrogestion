from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import User_dir
from compras.models import Requisicion, OrdenCompra
from django.contrib.auth.hashers import check_password
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from django.core.files.base import ContentFile
import io
import os
from datetime import datetime

def directivos_login(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        password = request.POST.get('password', '')

        if not nombre or not password:
            messages.error(request, 'Por favor complete todos los campos')
            return redirect('directivos_login')

        try:
            user_dir = User_dir.objects.get(nombre__exact=nombre)
            if user_dir.bloqueado:
                messages.error(request, 'Este usuario está bloqueado.')
                return redirect('directivos_login')
            if check_password(password, user_dir.password):
                request.session['user_dir_id'] = user_dir.id
                request.session['user_dir_nombre'] = user_dir.nombre
                return redirect('directivos_requisiciones')
            else:
                messages.error(request, 'Contraseña incorrecta')
        except User_dir.DoesNotExist:
            messages.error(request, 'Usuario no existe')
    return render(request, 'directivos_login.html')

@never_cache
def directivos_requisiciones(request):
    user_id = request.session.get('user_dir_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('directivos_login')
    try:
        user = User_dir.objects.get(id=user_id)
    except User_dir.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('directivos_login')

    requisiciones = Requisicion.objects.filter(directivo=user).order_by('-fecha_registro')

    buscar = request.GET.get('buscar', '').strip()
    estado = request.GET.get('estado', '').strip()
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if buscar:
        requisiciones = requisiciones.filter(codigo__icontains=buscar)
    if estado:
        requisiciones = requisiciones.filter(estado=estado)
    if fecha_desde:
        requisiciones = requisiciones.filter(fecha_registro__date__gte=fecha_desde)
    if fecha_hasta:
        requisiciones = requisiciones.filter(fecha_registro__date__lte=fecha_hasta)

    return render(request, 'directivos_requisiciones.html', {
        'user': user,
        'requisiciones': requisiciones,
    })

@require_POST
def firmar_requisicion(request, req_id):
    user_id = request.session.get('user_dir_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('directivos_login')
    req = get_object_or_404(Requisicion, id=req_id)
    user = get_object_or_404(User_dir, id=user_id)
    if req.estado == 'P':
        pdf_path = req.archivo.path
        firma_path = user.firma.path if user.firma else None

        if not firma_path or not os.path.exists(firma_path):
            messages.error(request, 'No se encontró la firma del directivo.')
            return redirect('directivos_requisiciones')

        pdf_reader = PdfReader(pdf_path)
        pdf_writer = PdfWriter()

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        firma_width = 3 * cm
        firma_height = 1.5 * cm
        page_width, page_height = letter
        x = (page_width - firma_width) / 2.5
        y = 2.7 * cm

        # Dibuja la imagen de la firma
        can.drawImage(firma_path, x, y, width=firma_width, height=firma_height, mask='auto')

        # Dibuja la fecha y hora de la firma debajo de la imagen
        fecha_firma = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        can.setFont("Helvetica", 10)
        can.drawString(x, y - 15, fecha_firma)

        can.save()
        packet.seek(0)
        firma_pdf = PdfReader(packet)

        for i in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[i]
            if i == len(pdf_reader.pages) - 1:
                page.merge_page(firma_pdf.pages[0])
            pdf_writer.add_page(page)

        output_stream = io.BytesIO()
        pdf_writer.write(output_stream)
        output_stream.seek(0)

        req.archivo_aprobacion.save(
            f"aprobacion_{req.codigo}.pdf",
            ContentFile(output_stream.read())
        )
        req.estado = 'A'
        req.save()
        messages.success(request, f'Requisición {req.codigo} aprobada/firmada y PDF firmado.')
    else:
        messages.info(request, 'La requisición ya fue aprobada o negada.')
    return redirect('directivos_requisiciones')

@never_cache
def directivos_ordenes(request):
    user_id = request.session.get('user_dir_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('directivos_login')
    try:
        user = User_dir.objects.get(id=user_id)
    except User_dir.DoesNotExist:
        messages.error(request, 'Usuario no encontrado')
        return redirect('directivos_login')

    # Filtrar órdenes de compra asociadas a esas requisiciones
    ordenes = OrdenCompra.objects.all().order_by('-fecha_creacion')

    buscar = request.GET.get('buscar', '').strip()
    estado = request.GET.get('estado', '').strip()

    if buscar:
        ordenes = ordenes.filter(codigo__icontains=buscar)
    if estado:
        ordenes = ordenes.filter(estado=estado)

    return render(request, 'directivos_ordenes.html', {
        'user': user,
        'ordenes_compra': ordenes,  # <-- Así el template funcionará bien
    })

@require_POST
def firmar_orden(request, orden_id):
    user_id = request.session.get('user_dir_id')
    if not user_id:
        messages.error(request, 'Debe iniciar sesión primero')
        return redirect('directivos_login')
    orden = get_object_or_404(OrdenCompra, id=orden_id)
    user = get_object_or_404(User_dir, id=user_id)
    if orden.estado == 'P':
        pdf_path = orden.archivo.path
        firma_path = user.firma.path if user.firma else None

        if not firma_path or not os.path.exists(firma_path):
            messages.error(request, 'No se encontró la firma del directivo.')
            return redirect('directivos_ordenes')

        pdf_reader = PdfReader(pdf_path)
        pdf_writer = PdfWriter()

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        firma_width = 3 * cm
        firma_height = 1.5 * cm
        page_width, page_height = letter
        x = (page_width - firma_width) / 2.5
        y = 2.7 * cm
        can.drawImage(firma_path, x, y, width=firma_width, height=firma_height, mask='auto')
        can.save()
        packet.seek(0)
        firma_pdf = PdfReader(packet)

        for i in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[i]
            if i == len(pdf_reader.pages) - 1:
                page.merge_page(firma_pdf.pages[0])
            pdf_writer.add_page(page)

        output_stream = io.BytesIO()
        pdf_writer.write(output_stream)
        output_stream.seek(0)

        orden.archivo_aprobacion.save(
            f"aprobacion_orden_{orden.codigo}.pdf",
            ContentFile(output_stream.read())
        )
        orden.estado = 'A'
        orden.save()
        messages.success(request, f'Orden {orden.codigo} aprobada/firmada y PDF firmado.')
    else:
        messages.info(request, 'La orden ya fue aprobada o negada.')
    return redirect('directivos_ordenes')

def logout(request):
    request.session.flush()  # Eliminar todas las sesiones
    return redirect('index')