import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

# --- Configuración de Rutas Relativas ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, 'data', 'reservas.json')
CONFIG_PATH = os.path.join(BASE_DIR, 'data', 'config.json')

HORAS_DISPONIBLES = [
    "08:00", "09:00", "10:00", "11:00", "12:00", 
    "14:00", "15:00", "16:00", "17:00", "18:00"
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

# --- Funciones de Configuración y I/O ---

def cargar_config():
    """Carga la configuración de la empresa desde el JSON."""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"empresa": "Mi Negocio", "email_admin": "diego251644@gmail.com"}
    except:
        return {"empresa": "Mi Negocio", "email_admin": "diego251644@gmail.com"}

def cargar_reservas():
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
    try:
        os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(reservas, f, ensure_ascii=False, indent=4)
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

# --- CORREOS ---

def enviar_correo_confirmacion(reserva, calendar_link, citas_link):
    config = cargar_config()
    empresa = config.get('empresa', 'Mi Negocio')
    destinatario = reserva.get('email')
    destinatario_admin = config.get('email_admin')
    
    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = f"{empresa} <{EMAIL_FROM}>"
        msg['To'] = destinatario
        msg['cc'] = destinatario_admin
        msg['Subject'] = f'📌 ¡Cita Confirmada! - {empresa}'
        
        html_body = f"""<div style="font-family:sans-serif; padding:20px; background:#f1f5f9;">
            <div style="background:white; border-radius:15px; max-width:500px; margin:auto; border:1px solid #e2e8f0; overflow:hidden;">
                <div style="background:#0ea5e9; padding:20px; text-align:center; color:white;"><h2>Cita Confirmada</h2></div>
                <div style="padding:20px;">
                    <p>
                        Hola <b>{reserva.get('nombre')}</b>,<br><br>
                        Tu cita para <b>{reserva.get('tipo_una')}</b> en <b>{empresa}</b> ha sido confirmada.<br>
                        📅 <b>Día:</b> {reserva.get('date')}<br>
                        ⏰ <b>Hora:</b> {reserva.get('hora')}<br><br>
                    </p>

                    <div style="text-align:center; margin:25px 0;">
                        <a href="{calendar_link}" style="background:#4285F4; color:white; padding:12px 25px; text-decoration:none; border-radius:10px; font-weight:bold; display:inline-block;">
                           📅 Agregar a Google Calendar
                        </a>
                         <a href="{citas_link}" style="background:#4285F4; color:white; padding:12px 25px; text-decoration:none; border-radius:10px; font-weight:bold; display:inline-block;">
                           📋 Ver Mis Citas
                        </a>
                    </div>

                    <p style="font-size:12px; color:#64748b; text-align:center;">
                        Si necesitas realizar algún cambio, comunícate con nosotros.
                    </p>
                </div>
            </div>
        </div>"""
        
        msg.attach(MIMEText(html_body, 'html'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT); server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD); server.send_message(msg); server.quit()
        return True
    except: return False

def enviar_correo_reagendacion(reserva, calendar_link,citas_link=None):
    config = cargar_config()
    empresa = config.get('empresa', '{{config.empresa}}')
    destinatario = reserva.get('email')
    destinatario_admin = config.get('email_admin')
    
    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = f"{empresa} <{EMAIL_FROM}>"
        msg['To'] = destinatario
        msg['cc'] = destinatario_admin
        msg['Subject'] = f'🕜 Cita Reagendada - {empresa}'
        html_body = f"""<div style="font-family:sans-serif; padding:20px; background:#fff7ed;">
            <div style="background:white; border-radius:15px; max-width:500px; margin:auto; border:1px solid #fed7aa; overflow:hidden;">
                <div style="background:#f59e0b; padding:20px; text-align:center; color:white;"><h2>Cita Reagendada</h2></div>
                <div style="padding:20px;">
                     <p>Hola <b>{reserva.get('nombre')}</b>,</p>
                    <p>Tu cita en <b>{empresa}</b> fue reprogramada con éxito. Te esperamos el <b>{reserva.get('date')}</b> a las <b>{reserva.get('hora')}</b>.</p>
                        <div style="text-align:center; margin:25px 0;">
                        <a href="{calendar_link}" style="background:#4285F4; color:white; padding:12px 25px; text-decoration:none; border-radius:10px; font-weight:bold; display:inline-block;">
                           📅 Agregar a Google Calendar
                        </a>
                    </div>
                    <p style="margin-top:20px; font-size:12px; color:#94a3b8;">Si no solicitaste este cambio, por favor comunícate con nosotros.</p>
                </div>
            </div>
        </div>"""
        msg.attach(MIMEText(html_body, 'html'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT); server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD); server.send_message(msg); server.quit()
        return True
    except: return False

def enviar_correo_cancelacion(reserva):
    config = cargar_config()
    empresa = config.get('empresa', '{{config.empresa}}')
    destinatario = reserva.get('email')
    destinatario_admin = config.get('email_admin')
    
    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = f"{empresa} <{EMAIL_FROM}>"
        msg['To'] = destinatario
        msg['cc'] = destinatario_admin
        msg['Subject'] = f'🚫 Cita Cancelada - {empresa}'
        
        html_body = f"""
        <div style="font-family:sans-serif; padding:20px; background:#fef2f2;">
            <div style="background:white; border-radius:15px; max-width:500px; margin:auto; border:1px solid #fecaca; overflow:hidden;">
                <div style="background:#ef4444; padding:20px; text-align:center; color:white;"><h2 style="margin:0;">Cita Cancelada</h2></div>
                <div style="padding:30px; color:#475569;">
                    <p>Hola <b>{reserva.get('nombre')}</b>,</p>
                    <p>Te informamos que tu cita en <b>{empresa}</b> para el día <b>{reserva.get('date')}</b> ha sido <b>cancelada</b>.</p>
                    <div style="background:#f8fafc; padding:15px; border-radius:10px; margin-top:20px;">
                        <p style="margin:0;"><b>Servicio:</b> {reserva.get('tipo_una')}</p>
                    </div>
                </div>
            </div>
        </div>"""
        msg.attach(MIMEText(html_body, 'html'))
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT); server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD); server.send_message(msg); server.quit()
        return True
    except: return False