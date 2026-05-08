import io
import os
import qrcode
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm

def generar_pdf_papeleta(papeleta):
    """
    Genera un archivo PDF para la estación de penitencia de San Gonzalo. 
    Se ha eliminado el escudo de fondo y se ha ampliado/subido el código QR.
    """
    buffer = io.BytesIO()
    width, height = A4
    p = canvas.Canvas(buffer, pagesize=A4)

    base = str(settings.BASE_DIR)
    assets_dir = os.path.abspath(os.path.join(base, "..", "frontend", "src", "assets"))
    
    fondo_path = os.path.join(assets_dir, "Papeleta2.jpg")

    if os.path.exists(fondo_path):
        p.drawImage(fondo_path, 0, 0, width=width, height=height)
    else:
        p.setFont("Helvetica", 14)
        p.setFillColor(colors.red)
        p.drawCentredString(width/2, height/2, f"Error: {fondo_path}")
        p.setFillColor(colors.black)

    url_validacion = f"{settings.FRONTEND_URL}/validar-acceso/{papeleta.id}/{papeleta.codigo_verificacion}"
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(url_validacion)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="#1a1a1a", back_color="white")

    color_texto = colors.HexColor("#1A1A1A")
    p.setFillColor(color_texto)

    y_cursor = height - 7.0 * cm
    
    p.saveState()
    p.translate(width / 2, y_cursor)
    p.scale(0.87, 1.0)
    
    p.setFont("Times-Bold", 11)
    p.drawCentredString(0, 0, "PONTIFICIA Y REAL HERMANDAD DEL SANTÍSIMO SACRAMENTO")
    
    p.setFont("Times-Bold", 10)
    p.drawCentredString(0, -0.5 * cm, "Y COFRADÍA DE NAZARENOS DE NUESTRO PADRE JESÚS EN SU SOBERANO PODER ANTE CAIFÁS,")
    
    p.setFont("Times-Bold", 11)
    p.drawCentredString(0, -1.0 * cm, "NUESTRA SEÑORA DE LA SALUD Y SAN JUAN EVANGELISTA")

    p.restoreState()

    p.setLineWidth(0.75)
    p.line(width * 0.30, y_cursor - 2.1 * cm, width * 0.70, y_cursor - 2.1 * cm)

    y_cursor -= 3.2 * cm 
    
    p.setFont("Times-Bold", 16)
    
    nombre_acto = papeleta.acto.nombre if (hasattr(papeleta, 'acto') and papeleta.acto) else "ACTO POR DETERMINAR"
    p.drawCentredString(width / 2, y_cursor, nombre_acto.upper())

    y_datos = y_cursor - 1.5 * cm 

    nombre_completo = f"{papeleta.hermano.nombre} {papeleta.hermano.primer_apellido} {papeleta.hermano.segundo_apellido}"
    p.setFont("Times-Bold", 15)
    p.drawCentredString(width / 2, y_datos, f"Hermano:  {nombre_completo.upper()}")

    p.setFont("Times-Bold", 15)
    p.drawCentredString(width / 2, y_datos - 0.8 * cm, f"D.N.I.:  {papeleta.hermano.dni}")

    y_sitio = y_datos - 2.8 * cm
    p.setFont("Times-Bold", 17)
    p.drawCentredString(width / 2, y_sitio, "ASIGNACIÓN DE PUESTO")

    p.setFont("Times-Roman", 15)

    nombre_puesto = papeleta.puesto.nombre if papeleta.puesto else "SITIO POR DETERMINAR"
    numero_pap = str(papeleta.numero_papeleta) if papeleta.numero_papeleta else "Pendiente"
    
    p.drawCentredString(width / 2, y_sitio - 1.0 * cm, f"Puesto:  {nombre_puesto}")
    p.drawCentredString(width / 2, y_sitio - 1.8 * cm, f"Nº de Papeleta:  {numero_pap}")

    if not papeleta.es_solicitud_insignia:
        y_dinamico = y_sitio - 2.6 * cm

        if papeleta.tramo and papeleta.tramo.numero_orden:
            p.drawCentredString(width / 2, y_dinamico, f"Tramo:  {papeleta.tramo.numero_orden}")
            y_dinamico -= 0.8 * cm

        if papeleta.orden_en_tramo:
            p.drawCentredString(width / 2, y_dinamico, f"Orden en el tramo:  {papeleta.orden_en_tramo}")

    y_qr = 5.5 * cm
    tam_qr = 4.5 * cm
    p.drawInlineImage(img_qr, (width/2) - (tam_qr/2), y_qr, width=tam_qr, height=tam_qr)
    
    p.setFont("Times-Bold", 9)
    p.drawCentredString(width/2, y_qr - 0.6 * cm, f"Código de Verificación: {papeleta.codigo_verificacion}")
    
    p.setFont("Times-Roman", 8)
    p.drawCentredString(width/2, y_qr - 1.1 * cm, "Valide la autenticidad de este documento escaneando el código QR.")

    p.setFont("Times-Italic", 8)
    p.drawCentredString(width/2, 1.2 * cm, "Documento personal e intransferible. Es obligatorio portarlo durante la Estación de Penitencia.")

    p.showPage()
    p.save()
    
    buffer.seek(0)
    return buffer