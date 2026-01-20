import io
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from django.utils.timezone import now

def generar_pdf_papeleta(papeleta):
    """
    Genera un archivo PDF en memoria (BytesIO) con los datos de la papeleta
    y un código QR de verificación.
    """
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # --- 1. Generación del Código QR ---
    # El contenido del QR puede ser el código de verificación o una URL de validación
    qr_content = f"ID:{papeleta.id}|VERIF:{papeleta.codigo_verificacion}|HERMANO:{papeleta.hermano.dni}"
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(qr_content)
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