from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import User_dir
from compras.models import Requisicion
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

    requisiciones = Requisicion.objects.all().order_by('-fecha_registro')

    buscar = request.GET.get('buscar', '').strip()
    estado = request.GET.get('estado', '').strip()

    if buscar:
        requisiciones = requisiciones.filter(codigo__icontains=buscar)
    if estado:
        requisiciones = requisiciones.filter(estado=estado)

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
        # Ruta del PDF original
        pdf_path = req.archivo.path
        # Ruta de la firma
        firma_path = user.firma.path if user.firma else None

        if not firma_path or not os.path.exists(firma_path):
            messages.error(request, 'No se encontró la firma del directivo.')
            return redirect('directivos_requisiciones')

        # Leer el PDF original
        pdf_reader = PdfReader(pdf_path)
        pdf_writer = PdfWriter()

        # Crear un PDF temporal con la firma usando reportlab
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        # Dimensiones de la firma en puntos (1 cm = 28.35 pt)
        firma_width = 3 * cm
        firma_height = 1.5 * cm
        # Posición: centrado en la parte inferior
        page_width, page_height = letter
        x = (page_width - firma_width) / 2.5
        y = 2.7 * cm  # 2.7 cm desde abajo
        can.drawImage(firma_path, x, y, width=firma_width, height=firma_height, mask='auto')
        can.save()
        packet.seek(0)
        firma_pdf = PdfReader(packet)

        # Fusionar la firma en la última página del PDF original
        for i in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[i]
            if i == len(pdf_reader.pages) - 1:
                page.merge_page(firma_pdf.pages[0])
            pdf_writer.add_page(page)

        # Guardar el PDF firmado en memoria
        output_stream = io.BytesIO()
        pdf_writer.write(output_stream)
        output_stream.seek(0)

        # Sobrescribir el archivo original o guardar como archivo de aprobación
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
