import io
import qrcode
from django.conf import settings  # <--- IMPORTANTE: Necesario para acceder a FRONTEND_URL
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from django.utils.timezone import now
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404

from api.models import PapeletaSitio

def generar_pdf_papeleta(papeleta):
    """
    Genera un archivo PDF en memoria (BytesIO) con los datos de la papeleta
    y un código QR de verificación que apunta a la URL de validación.
    """
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # --- 1. Generación del Código QR ---
    # CAMBIO: El QR ahora es un enlace al Frontend para validación automática
    # Estructura: DOMINIO/validar-acceso/:id_papeleta/:codigo_verificacion
    
    # Asegúrate de tener FRONTEND_URL en tu settings.py (ej: "http://192.168.1.35:5173")
    url_validacion = f"{settings.FRONTEND_URL}/validar-acceso/{papeleta.id}/{papeleta.codigo_verificacion}"
    
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(url_validacion)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="black", back_color="white")

    # --- 2. Diseño del PDF (Maquetación) ---
    
    # Marco decorativo
    p.setLineWidth(3)
    p.setStrokeColorRGB(0.3, 0.1, 0.3)  # Un color morado cofrade
    p.rect(1 * cm, 1 * cm, width - 2 * cm, height - 2 * cm)

    # Cabecera
    p.setFont("Helvetica-Bold", 20)
    p.drawCentredString(width / 2, height - 3 * cm, "HERMANDAD DE SAN GONZALO")
    p.setFont("Helvetica", 12)
    p.drawCentredString(width / 2, height - 3.8 * cm, "SEVILLA")
    
    p.line(3 * cm, height - 4.2 * cm, width - 3 * cm, height - 4.2 * cm)

    # Título del documento
    p.setFont("Helvetica-Bold", 24)
    p.drawCentredString(width / 2, height - 6 * cm, "PAPELETA DE SITIO")
    p.setFont("Helvetica", 16)
    p.drawCentredString(width / 2, height - 7 * cm, f"ESTACIÓN DE PENITENCIA {papeleta.anio}")

    # Datos del Hermano
    y_position = height - 10 * cm
    p.setFont("Helvetica", 14)
    p.drawString(3 * cm, y_position, f"Hermano: {papeleta.hermano.nombre} {papeleta.hermano.primer_apellido} {papeleta.hermano.segundo_apellido}")
    p.drawString(3 * cm, y_position - 1.5 * cm, f"D.N.I.: {papeleta.hermano.dni}")

    # Datos del Sitio
    p.setFont("Helvetica-Bold", 16)
    nombre_puesto = papeleta.puesto.nombre if papeleta.puesto else "SITIO POR DETERMINAR"
    p.drawString(3 * cm, y_position - 4 * cm, f"Sitio Asignado: {nombre_puesto}")
    
    if papeleta.tramo:
        p.setFont("Helvetica", 14)
        p.drawString(3 * cm, y_position - 5 * cm, f"Ubicación: {papeleta.tramo.nombre}")

    if papeleta.numero_papeleta:
         p.drawString(3 * cm, y_position - 6 * cm, f"Nº de Cirio/Insignia: {papeleta.numero_papeleta}")

    # Pie de página y QR
    # Guardamos la imagen QR temporalmente en el canvas
    p.drawInlineImage(img_qr, width - 8 * cm, 3 * cm, width=5 * cm, height=5 * cm)
    
    p.setFont("Helvetica", 10)
    p.drawString(3 * cm, 5 * cm, "Código de Verificación:")
    p.setFont("Courier-Bold", 12)
    p.drawString(3 * cm, 4.5 * cm, str(papeleta.codigo_verificacion))
    
    p.setFont("Helvetica-Oblique", 8)
    p.drawCentredString(width / 2, 2 * cm, "Este documento es personal e intransferible. Debe portarlo durante la Estación de Penitencia.")

    # Finalizar página y guardar
    p.showPage()
    p.save()
    
    # Rebobinar el buffer para que esté listo para lectura
    buffer.seek(0)
    return buffer




def validar_acceso_papeleta(papeleta_id, codigo_verificacion, usuario_escaneador):
    """
    Valida la papeleta y cambia el estado a LEIDA.
    """
    # 1. Seguridad: Solo admins o diputados pueden validar (ajusta según tu lógica)
    if not usuario_escaneador.is_staff and not usuario_escaneador.esAdmin:
        raise PermissionDenied("No tienes permisos para validar accesos.")

    # 2. Buscar papeleta
    papeleta = get_object_or_404(PapeletaSitio, pk=papeleta_id)

    # 3. Verificar código de seguridad (evita que alguien cambie el ID en la URL manualmente)
    if str(papeleta.codigo_verificacion) != str(codigo_verificacion):
        raise ValidationError("El código de verificación no es válido.")

    # 4. Validar estado actual
    if papeleta.estado_papeleta == PapeletaSitio.EstadoPapeleta.LEIDA:
        return {
            "status": "warning", 
            "mensaje": f"Esta papeleta YA FUE LEÍDA anteriormente ({papeleta.fecha_emision}).",
            "papeleta": papeleta
        }

    if papeleta.estado_papeleta not in [PapeletaSitio.EstadoPapeleta.EMITIDA, PapeletaSitio.EstadoPapeleta.RECOGIDA]:
        raise ValidationError(f"La papeleta no está activa (Estado: {papeleta.estado_papeleta}).")

    # 5. ACTUALIZAR ESTADO
    papeleta.estado_papeleta = PapeletaSitio.EstadoPapeleta.LEIDA
    papeleta.save()

    return {
        "status": "success",
        "mensaje": "Acceso Correcto. Papeleta marcada como LEÍDA.",
        "papeleta": papeleta
    }