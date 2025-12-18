import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# --- Configuración Compartida ---
RESERVAS_FILE = "reservas.json"
HORAS_DISPONIBLES = [
    "08:00", "09:00", "10:00", "11:00", "12:00", 
    "14:00", "15:00", "16:00", "17:00"
]
DURACION_SERVICIOS = {
    "Semipermanente": 60,
    "Soft Gel": 120,
    "Poly Gel": 120,
    "Base Rubber": 60,
    "Decoración": 60,
}

# Configuración para correo
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_FROM = 'citareservar@gmail.com' 
EMAIL_PASSWORD = 'dren psgm ncqx lrpy' 

# --- Funciones de I/O ---
def cargar_reservas():
    """Carga todas las reservas desde el archivo JSON."""
    if os.path.exists(RESERVAS_FILE):
        try:
            with open(RESERVAS_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                if not content: return []
                return json.loads(content)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error al cargar: {e}")
            return []
    return []

def guardar_reservas(reservas):
    """Guarda la lista de reservas en el archivo JSON."""
    with open(RESERVAS_FILE, "w", encoding="utf-8") as f:
        json.dump(reservas, f, indent=4, ensure_ascii=False)

# --- Funciones de formato ---
def format_google_calendar_datetime(date_str, time_str, duration_minutes):
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        start = dt.strftime("%Y%m%dT%H%M%S")
        end = (dt + timedelta(minutes=duration_minutes)).strftime("%Y%m%dT%H%M%S")
        return start, end
    except:
        return "", ""

def normalizar_fecha(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")

def normalizar_hora(hora_str):
    return datetime.strptime(hora_str, "%H:%M").strftime("%H:%M")

# --- Lógica de Validación ---
def get_horas_ocupadas_por_superposicion(reservas, fecha_a_mostrar):
    horas_ocupadas = set()
    reservas_del_dia = [r for r in reservas if r.get("date") == fecha_a_mostrar]
    for r in reservas_del_dia:
        try:
            inicio = datetime.strptime(f"{fecha_a_mostrar} {r['hora']}", "%Y-%m-%d %H:%M")
            duracion = r.get("duracion", 60)
            fin = inicio + timedelta(minutes=duracion)
            for h_disp in HORAS_DISPONIBLES:
                posible = datetime.strptime(f"{fecha_a_mostrar} {h_disp}", "%Y-%m-%d %H:%M")
                if inicio <= posible < fin:
                    horas_ocupadas.add(h_disp)
        except: continue
    return horas_ocupadas

def check_new_reservation_overlap(reservas, fecha_propuesta, hora_propuesta, duracion_minutos):
    try:
        inicio_p = datetime.strptime(f"{fecha_propuesta} {hora_propuesta}", "%Y-%m-%d %H:%M")
        fin_p = inicio_p + timedelta(minutes=duracion_minutos)
        if fin_p.hour >= 18 and fin_p.minute > 0: return True
        if hora_propuesta not in HORAS_DISPONIBLES: return True
        
        for r in [res for res in reservas if res.get("date") == fecha_propuesta]:
            inicio_e = datetime.strptime(f"{r['date']} {r['hora']}", "%Y-%m-%d %H:%M")
            fin_e = inicio_e + timedelta(minutes=r.get("duracion", 60))
            if (inicio_p < fin_e) and (fin_p > inicio_e): return True
        return False
    except: return True

# --- Función de Correo ---
def enviar_correo_confirmacion(reserva, calendar_link, cancel_link):
    """Envía el correo de confirmación de reserva al cliente con diseño profesional."""
    destinatario = reserva.get('email')
    nombre = reserva.get('nombre')
    tipo_una = reserva.get('tipo_una')
    fecha = reserva.get('date')
    hora = reserva.get('hora')
    duration_minutes = reserva.get('duracion', 60)
    
    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = f"Editar empresa <{EMAIL_FROM}>"
        msg['To'] = destinatario
        msg['Subject'] = '✨ ¡Tu Cita ha sido Confirmada! - Editar empresa' #nombre de la empresa

        duracion_legible = f"{duration_minutes // 60}h {duration_minutes % 60}m"
        
        # Diseño recuperado de la imagen
        html_body = f"""
        <html>
            <body style="font-family: sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="background-color: white; padding: 30px; border-radius: 12px; max-width: 600px; margin: auto; border-top: 6px solid #e91e63; shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h2 style="color: #e91e63; font-size: 24px; margin-bottom: 20px;">¡Tu Cita ha sido Confirmada!</h2>
                    
                    <p style="font-size: 16px; color: #333;">Hola <b>{nombre}</b>,</p>
                    <p style="font-size: 16px; color: #333;">Hemos agendado tu cita de <b>{tipo_una}</b> con éxito para el siguiente horario:</p>
                    
                    <div style="background-color: #f9f9f9; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 10px 0; font-size: 16px;">🗓 <b>Fecha:</b> {fecha}</p>
                        <p style="margin: 10px 0; font-size: 16px;">⏰ <b>Hora:</b> {hora}</p>
                        <p style="margin: 10px 0; font-size: 16px;">⏳ <b>Duración Estimada:</b> {duracion_legible}</p>
                    </div>
                    
                    <p style="font-size: 14px; color: #666;">Añade esta cita a tu calendario o cancélala si es necesario:</p>

                    <table role="presentation" border="0" cellpadding="0" cellspacing="0" style="width: 100%; margin-top: 20px;">
                        <tr>
                            <td style="text-align: center; padding: 10px;">
                                <a href="{calendar_link}" target="_blank"
                                   style="background-color:#007bff; color:white; padding:12px 18px; text-decoration:none; border-radius:8px; display:inline-block; font-weight:bold; font-size: 14px;">
                                    ➕ Agregar a Google Calendar
                                </a>
                            </td>
                            <td style="text-align: center; padding: 10px;">
                                <a href="{cancel_link}" target="_blank"
                                   style="background-color:#dc3545; color:white; padding:12px 18px; text-decoration:none; border-radius:8px; display:inline-block; font-weight:bold; font-size: 14px;">
                                    ❌ Cancelar Cita
                                </a>
                            </td>
                        </tr>
                    </table>
                    
                    <p style="font-size: 12px; color: #888; margin-top: 25px; border-top: 1px solid #eee; padding-top: 15px; text-align: center;">
                        Si cancelas la cita, el horario se liberará automáticamente.<br>
                        ¡Gracias por agendar con <b>Editar Empresa</b>!
                    </p>
                </div>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Conexión y envío
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Error al enviar el correo a {destinatario}: {e}")
        return False