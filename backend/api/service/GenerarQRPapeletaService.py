import io
import os
import qrcode
from django.conf import settings
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm
from django.utils.timezone import now
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404

from api.models import PapeletaSitio

def generar_pdf_papeleta(papeleta):
    """
    Genera un archivo PDF para la estación de penitencia de San Gonzalo. 
    Se utiliza una marca de agua central y una cabecera extendida para 
    albergar el título completo de la corporación con rigor formal.
    """
    buffer = io.BytesIO()
    width, height = A4
    p = canvas.Canvas(buffer, pagesize=A4)

    # --- Configuración de Rutas de Activos ---
    base = str(settings.BASE_DIR)
    assets_dir = os.path.abspath(os.path.join(base, "..", "frontend", "src", "assets"))
    
    fondo_path = os.path.join(assets_dir, "Papeleta2.jpg")
    escudo_path = os.path.join(assets_dir, "escudo.png")

    # --- 1. Capa de Fondo (Papeleta2.jpg) ---
    if os.path.exists(fondo_path):
        p.drawImage(fondo_path, 0, 0, width=width, height=height)
    else:
        p.setFont("Helvetica", 14)
        p.setFillColor(colors.red)
        p.drawCentredString(width/2, height/2, f"Error: {fondo_path}")
        p.setFillColor(colors.black)

    # --- 1.5 Marca de Agua (Escudo central) ---
    if os.path.exists(escudo_path):
        tamano_marca = 14 * cm
        
        p.saveState()          
        p.setFillAlpha(0.10)   
        
        p.drawImage(
            escudo_path, 
            (width - tamano_marca) / 2, 
            (height - tamano_marca) / 2 + 1.0 * cm,
            width=tamano_marca, 
            height=tamano_marca, 
            preserveAspectRatio=True, 
            mask='auto'
        )
        
        p.restoreState()       

    # --- 2. Código QR ---
    url_validacion = f"{settings.FRONTEND_URL}/validar-acceso/{papeleta.id}/{papeleta.codigo_verificacion}"
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(url_validacion)
    qr.make(fit=True)
    img_qr = qr.make_image(fill_color="#1a1a1a", back_color="white")

    color_texto = colors.HexColor("#1A1A1A")
    p.setFillColor(color_texto)

    # --- 3. Cabecera con Nombre Completo de la Hermandad ---
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

    # --- 4. Título del Documento (Nombre del Acto) ---
    y_cursor -= 3.2 * cm 
    
    p.setFont("Times-Bold", 16)
    
    nombre_acto = papeleta.acto.nombre if (hasattr(papeleta, 'acto') and papeleta.acto) else "ACTO POR DETERMINAR"
    p.drawCentredString(width / 2, y_cursor, nombre_acto.upper())

    # --- 5. Datos del Hermano ---
    margen_izq = 4 * cm
    y_datos = y_cursor - 1.5 * cm 

    p.setFont("Times-Bold", 12)
    p.drawString(margen_izq + 0.5 * cm, y_datos, "Hermano/a:")
    
    p.setFont("Times-Roman", 12)
    nombre_completo = f"{papeleta.hermano.nombre} {papeleta.hermano.primer_apellido} {papeleta.hermano.segundo_apellido}"
    p.drawString(margen_izq + 3.0 * cm, y_datos, nombre_completo.upper())

    p.setFont("Times-Bold", 12)
    p.drawString(margen_izq + 0.5 * cm, y_datos - 1.0 * cm, "D.N.I.:")
    p.setFont("Times-Roman", 12)
    p.drawString(margen_izq + 3.0 * cm, y_datos - 1.0 * cm, papeleta.hermano.dni)

    # --- 6. Datos del Sitio (Con lógica de Insignia vs Cirio) ---
    y_sitio = y_datos - 3.5 * cm
    p.setFont("Times-Bold", 14)
    p.drawString(margen_izq, y_sitio, "ASIGNACIÓN DE PUESTO")

    p.setFont("Times-Roman", 12)
    
    # 1. Datos comunes siempre visibles
    nombre_puesto = papeleta.puesto.nombre if papeleta.puesto else "SITIO POR DETERMINAR"
    numero_pap = str(papeleta.numero_papeleta) if papeleta.numero_papeleta else "Pendiente"
    
    p.drawString(margen_izq + 0.5 * cm, y_sitio - 1.0 * cm, f"Puesto:  {nombre_puesto}")
    p.drawString(margen_izq + 0.5 * cm, y_sitio - 1.8 * cm, f"Nº de Papeleta:  {numero_pap}")

    # 2. Datos específicos si NO es solicitud de insignia (es_solicitud_insignia = False/0)
    if not papeleta.es_solicitud_insignia:
        y_dinamico = y_sitio - 2.6 * cm
        
        # Mostrar el número de orden del tramo
        if papeleta.tramo and papeleta.tramo.numero_orden:
            p.drawString(margen_izq + 0.5 * cm, y_dinamico, f"Tramo (Nº Orden):  {papeleta.tramo.numero_orden}")
            y_dinamico -= 0.8 * cm
            
        # Mostrar el orden específico en el tramo
        if papeleta.orden_en_tramo:
            p.drawString(margen_izq + 0.5 * cm, y_dinamico, f"Orden en el tramo:  {papeleta.orden_en_tramo}")

    # --- 7. Firmas ---
    y_firmas = 8.5 * cm
    p.setLineWidth(0.5)
    p.line(margen_izq, y_firmas, margen_izq + 4.5 * cm, y_firmas)
    p.setFont("Times-Italic", 11)
    p.drawCentredString(margen_izq + 2.25 * cm, y_firmas - 0.6 * cm, "El Diputado Mayor de Gobierno")

    p.line(width - margen_izq - 4.5 * cm, y_firmas, width - margen_izq, y_firmas)
    p.drawCentredString(width - margen_izq - 2.25 * cm, y_firmas - 0.6 * cm, "El Hermano")

    # --- 8. Pie y QR ---
    y_qr = 3.5 * cm
    p.drawInlineImage(img_qr, (width/2) - 1.5 * cm, y_qr, width=3 * cm, height=3 * cm)
    
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