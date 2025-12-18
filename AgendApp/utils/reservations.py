import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# --- Configuración de Rutas Relativas ---
# Esto asegura que el archivo siempre se guarde en la carpeta 'data' del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, 'data', 'reservas.json')

HORAS_DISPONIBLES = [
    "08:00", "09:00", "10:00", "11:00", "12:00", 
    "14:00", "15:00", "16:00", "17:00", "18:00", "19:00", "20:00"
]

DURACION_SERVICIOS = {
    "Semipermanente": 60,
    "Soft Gel": 120,
    "Poly Gel": 120,
    "Base Rubber": 60,
    "Decoración": 60,
}

SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL_FROM = 'citareservar@gmail.com' 
EMAIL_PASSWORD = 'dren psgm ncqx lrpy' 

# --- Funciones de I/O Corregidas ---
def cargar_reservas():
    """Carga todas las reservas desde el archivo JSON de forma segura."""
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content: return []
                return json.loads(content)
        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️ Error al cargar: {e}")
            return []
    return []

def guardar_reservas(reservas):
    """Guarda la lista completa de reservas en el archivo JSON."""
    try:
        # Asegura que la carpeta 'data' exista
        os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(reservas, f, ensure_ascii=False, indent=4)
        print(f"✅ Reservas guardadas exitosamente en {JSON_PATH}")
    except Exception as e:
        print(f"❌ Error al guardar reservas: {e}")

# --- Funciones de Utilidad ---
def format_google_calendar_datetime(date_str, time_str, duration_minutes):
    try:
        dt = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        start = dt.strftime("%Y%m%dT%H%M%S")
        end = (dt + timedelta(minutes=duration_minutes)).strftime("%Y%m%dT%H%M%S")
        return start, end
    except: return "", ""

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

def enviar_correo_confirmacion(reserva, calendar_link, cancel_link):
    destinatario = reserva.get('email')
    nombre = reserva.get('nombre')
    tipo_una = reserva.get('tipo_una')
    fecha = reserva.get('date')
    hora = reserva.get('hora')
    duration_minutes = reserva.get('duracion', 60)
    
    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = f"AgendApp - Cocoa Nails <{EMAIL_FROM}>"
        msg['To'] = destinatario
        msg['Subject'] = '✨ ¡Cita Confirmada! - Cocoa Nails'

        duracion_legible = f"{duration_minutes // 60}h {duration_minutes % 60}m"
        
        html_body = f"""
        <html>
            <body style="font-family: sans-serif; background-color: #f8fafc; padding: 20px;">
                <div style="background-color: white; padding: 30px; border-radius: 20px; max-width: 600px; margin: auto; border: 1px solid #e2e8f0;">
                    <h2 style="color: #0ea5e9; font-size: 24px;">¡Tu cita está lista!</h2>
                    <p>Hola <b>{nombre}</b>, AgendApp ha procesado tu reserva en Cocoa Nails:</p>
                    <div style="background-color: #f1f5f9; padding: 15px; border-radius: 12px; margin: 20px 0;">
                        <p>🗓 <b>Fecha:</b> {fecha} | ⏰ <b>Hora:</b> {hora}</p>
                        <p>💅 <b>Servicio:</b> {tipo_una} ({duracion_legible})</p>
                    </div>
                    <div style="text-align: center; margin-top: 30px;">
                        <a href="{calendar_link}" style="background-color:#0ea5e9; color:white; padding:12px 20px; text-decoration:none; border-radius:10px; font-weight:bold; margin-right: 10px;">Google Calendar</a>
                        <a href="{cancel_link}" style="background-color:#ef4444; color:white; padding:12px 20px; text-decoration:none; border-radius:10px; font-weight:bold;">Cancelar Cita</a>
                    </div>
                </div>
            </body>
        </html>
        """
        msg.attach(MIMEText(html_body, 'html'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Error correo: {e}")
        return False