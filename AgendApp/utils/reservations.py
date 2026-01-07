import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, 'data', 'reservas.json')
CONFIG_PATH = os.path.join(BASE_DIR, 'data', 'config.json')

# --- Funciones de Configuración y I/O ---


def formatear_hora_12h(hora_24):
    """Convierte '14:00' a '02:00 PM'"""
    try:
        dt = datetime.strptime(hora_24, "%H:%M")
        return dt.strftime("%I:%M %p")
    except:
        return hora_24
    

# --- MODIFICACIÓN EN CARGAR_CONFIG ---
def cargar_config():
    """Carga la configuración desde el JSON o devuelve valores por defecto."""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Error cargando config: {e}")
    
    # Valores de respaldo por si el archivo no existe o está mal escrito
    return {
        "empresa": "Mi Negocio", 
        "email_admin": "admin@mail.com",
        "horarios_base": ["08:00", "09:00", "10:00"],
        "servicios": {"General": 60}
    }

# --- ESTAS VARIABLES AHORA SON DINÁMICAS ---
# Reemplaza donde uses HORAS_DISPONIBLES y DURACION_SERVICIOS por esto:
config_data = cargar_config()
HORAS_DISPONIBLES = config_data.get("horarios_base", [])
DURACION_SERVICIOS = config_data.get("servicios", {})

# --- MODIFICACIÓN EN LAS FUNCIONES DE CORREO ---
def enviar_correo_generico(msg, config):
    """Función auxiliar para no repetir código de envío"""
    smtp_conf = config.get('smtp', {})
    try:
        server = smtplib.SMTP(smtp_conf.get('server'), smtp_conf.get('port'))
        server.starttls()
        server.login(smtp_conf.get('email'), smtp_conf.get('password'))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error SMTP: {e}")
        return False

# Ejemplo de cómo queda ahora enviar_correo_confirmacion:
def enviar_correo_confirmacion(reserva, calendar_link, citas_link):
    config = cargar_config()
    empresa = config.get('empresa')
    smtp_conf = config.get('smtp', {})
    
    destinatario = reserva.get('email')
    
    try:
        msg = MIMEMultipart("alternative")
        # Usamos el email configurado en el JSON
        msg['From'] = f"{empresa} <{smtp_conf.get('email')}>" 
        msg['To'] = destinatario
        msg['Subject'] = f'📌 ¡Cita Confirmada! - {empresa}'
        
        # ... (aquí va tu html_body igual que antes) ...
        
        return enviar_correo_generico(msg, config)
    except:
        return False

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
    # CARGAR CONFIG AQUÍ PARA QUE SEA TIEMPO REAL
    config = cargar_config()
    horas_base = config.get("horarios_base", []) 
    
    horas_ocupadas = set()
    reservas_del_dia = [r for r in reservas if r.get("date") == fecha_a_mostrar]
    
    for r in reservas_del_dia:
        try:
            inicio = datetime.strptime(f"{fecha_a_mostrar} {r['hora']}", "%Y-%m-%d %H:%M")
            duracion = r.get("duracion", 60)
            fin = inicio + timedelta(minutes=duracion)
            
            # USAR LAS HORAS DEL JSON
            for h_disp in horas_base:
                posible = datetime.strptime(f"{fecha_a_mostrar} {h_disp}", "%Y-%m-%d %H:%M")
                if inicio <= posible < fin:
                    horas_ocupadas.add(h_disp)
        except: continue
    return horas_ocupadas

# --- CORREOS ---

def enviar_correo_confirmacion(reserva, calendar_link, citas_link):
    config = cargar_config()
    empresa = config.get('empresa', 'Mi Negocio')
    wpp = config.get('whatsapp', '')
    smtp_conf = config.get('smtp', {})
    
    # Bloque de Publicidad y Notas (Footer)
# Bloque de Publicidad y Notas (Footer) actualizado
    footer_html = f"""
        <div style="margin-top:20px; padding-top:20px; border-top:1px solid #e2e8f0; color:#475569; font-size:13px;">
            <p>⚠️ <b>Recordatorio importante:</b> Por favor, llega <b>15 minutos antes</b> de tu cita. 
            Si no puedes llegar a tiempo, avísanos por WhatsApp: 
            <a href="https://wa.me/{wpp}" style="color:#25D366; font-weight:bold; text-decoration:none;">📱 Chatear ahora</a></p>
            
            <hr style="border:none; border-top:1px solid #f1f5f9; margin:20px 0;">
            
            <div style="text-align:center; background:#f0f9ff; padding:15px; border-radius:12px; border:1px solid #e0f2fe;">
                <p style="margin:0; font-weight:bold; color:#0ea5e9; font-size:14px;">✨ Potenciado por AgendApp</p>
                <p style="margin:5px 0 10px 0; font-size:12px; color:#64748b;">¿Quieres un sistema de reservas como este?</p>
                <a href="https://agendapp.co" style="background:#0ea5e9; color:white; padding:6px 15px; text-decoration:none; border-radius:8px; font-size:11px; font-weight:bold; display:inline-block;">
                    🚀 Visítanos en agendapp.co
                </a>
            </div>
            
            <p style="text-align:center; font-size:11px; color:#94a3b8; margin-top:15px;">
                📧 Este es un correo informativo automático. Por favor, <b>no respondas a este mensaje</b>.
            </p>
        </div>
    """

    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = f"{empresa} <{smtp_conf.get('email')}>"
        msg['To'] = reserva.get('email')
        msg['cc'] = config.get('email_admin')
        msg['Subject'] = f'📌 ¡Cita Confirmada! - {empresa}'
        
        html_body = f"""<div style="font-family:sans-serif; padding:20px; background:#f1f5f9;">
            <div style="background:white; border-radius:15px; max-width:500px; margin:auto; border:1px solid #e2e8f0; overflow:hidden;">
                <div style="background:#0ea5e9; padding:20px; text-align:center; color:white;"><h2 style="margin:0;">Cita Confirmada</h2></div>
                <div style="padding:20px;">
                    <p>Hola <b>{reserva.get('nombre')}</b>,</p>
                    <p>Tu cita para <b>{reserva.get('tipo_una')}</b> ha sido agendada con éxito.</p>
                    <p>📅 <b>Día:</b> {reserva.get('date')}<br>⏰ <b>Hora:</b> {reserva.get('hora')}</p>
                    
                    <div style="text-align:center; margin:25px 0;">
                        <a href="{calendar_link}" style="background:#4285F4; color:white; padding:12px 25px; text-decoration:none; border-radius:10px; font-weight:bold; display:inline-block; margin-bottom:10px;">📅 Google Calendar</a>
                        <a href="{citas_link}" style="background:#64748b; color:white; padding:12px 25px; text-decoration:none; border-radius:10px; font-weight:bold; display:inline-block;">📋 Ver Mis Citas</a>
                    </div>
                    {footer_html}
                </div>
            </div>
                 <div style="text-align:center; background:#f0f9ff; padding:15px; border-radius:12px; border:1px solid #e0f2fe;">
                <p style="margin:0; font-weight:bold; color:#0ea5e9; font-size:14px;">✨ Potenciado por AgendApp</p>
                <p style="margin:5px 0 10px 0; font-size:12px; color:#64748b;">¿Quieres un sistema de reservas como este?</p>
                <a href="https://agendapp.co" style="background:#0ea5e9; color:white; padding:6px 15px; text-decoration:none; border-radius:8px; font-size:11px; font-weight:bold; display:inline-block;">
                    🚀 Visítanos en agendapp.co
                </a>
            </div>
            
            <p style="text-align:center; font-size:11px; color:#94a3b8; margin-top:15px;">
                📧 Este es un correo informativo automático. Por favor, <b>no respondas a este mensaje</b>.
            </p>
        </div>
        </div>"""
        
        msg.attach(MIMEText(html_body, 'html'))
        server = smtplib.SMTP(smtp_conf.get('server'), smtp_conf.get('port'))
        server.starttls()
        server.login(smtp_conf.get('email'), smtp_conf.get('password'))
        server.send_message(msg); server.quit()
        return True
    except Exception as e:
        print(f"Error: {e}"); return False

def enviar_correo_reagendacion(reserva, calendar_link, citas_link=None):
    config = cargar_config()
    empresa = config.get('empresa', 'Mi Negocio')
    smtp_conf = config.get('smtp', {})
    
    destinatario = reserva.get('email')
    destinatario_admin = config.get('email_admin')
    
    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = f"{empresa} <{smtp_conf.get('email')}>"
        msg['To'] = destinatario
        msg['cc'] = destinatario_admin
        msg['Subject'] = f'Cita Reagendada - {empresa}'

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
                <div style="text-align:center; background:#f0f9ff; padding:15px; border-radius:12px; border:1px solid #e0f2fe;">
                <p style="margin:0; font-weight:bold; color:#0ea5e9; font-size:14px;">✨ Potenciado por AgendApp</p>
                <p style="margin:5px 0 10px 0; font-size:12px; color:#64748b;">¿Quieres un sistema de reservas como este?</p>
                <a href="https://agendapp.co" style="background:#0ea5e9; color:white; padding:6px 15px; text-decoration:none; border-radius:8px; font-size:11px; font-weight:bold; display:inline-block;">
                    🚀 Visítanos en agendapp.co
                </a>
            </div>
            
            <p style="text-align:center; font-size:11px; color:#94a3b8; margin-top:15px;">
                📧 Este es un correo informativo automático. Por favor, <b>no respondas a este mensaje</b>.
            </p>
        </div>
            </div>
        </div>"""
        msg.attach(MIMEText(html_body, 'html'))

        # Conexión SMTP dinámica
        server = smtplib.SMTP(smtp_conf.get('server'), smtp_conf.get('port'))
        server.starttls()
        server.login(smtp_conf.get('email'), smtp_conf.get('password'))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error reagendando: {e}")
        return False

def enviar_correo_cancelacion(reserva):
    config = cargar_config()
    empresa = config.get('empresa', 'Mi Negocio')
    smtp_conf = config.get('smtp', {})
    
    destinatario = reserva.get('email')
    destinatario_admin = config.get('email_admin')
    
    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = f"{empresa} <{smtp_conf.get('email')}>"
        msg['To'] = destinatario
        msg['cc'] = destinatario_admin
        msg['Subject'] = f'Cita Cancelada - {empresa}'
        
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
                    <div style="text-align:center; background:#f0f9ff; padding:15px; border-radius:12px; border:1px solid #e0f2fe;">
                <p style="margin:0; font-weight:bold; color:#0ea5e9; font-size:14px;">✨ Potenciado por AgendApp</p>
                <p style="margin:5px 0 10px 0; font-size:12px; color:#64748b;">¿Quieres un sistema de reservas como este?</p>
                <a href="https://agendapp.co" style="background:#0ea5e9; color:white; padding:6px 15px; text-decoration:none; border-radius:8px; font-size:11px; font-weight:bold; display:inline-block;">
                    🚀 Visítanos en agendapp.co
                </a>
            </div>
            
            <p style="text-align:center; font-size:11px; color:#94a3b8; margin-top:15px;">
                📧 Este es un correo informativo automático. Por favor, <b>no respondas a este mensaje</b>.
            </p>
        </div>
                </div>
            </div>
        </div>"""
        msg.attach(MIMEText(html_body, 'html'))

        # Conexión SMTP dinámica
        server = smtplib.SMTP(smtp_conf.get('server'), smtp_conf.get('port'))
        server.starttls()
        server.login(smtp_conf.get('email'), smtp_conf.get('password'))
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Error cancelando: {e}")
        return False