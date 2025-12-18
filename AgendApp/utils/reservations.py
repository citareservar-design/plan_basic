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
    destinatario_admin = 'diego251644@gmail.com'
    nombre = reserva.get('nombre')
    tipo_una = reserva.get('tipo_una')
    fecha = reserva.get('date')
    hora = reserva.get('hora')
    duration_minutes = reserva.get('duracion', 60)
    
    try:
        msg = MIMEMultipart("alternative")
        msg['From'] = f"AgendApp - Editar empresa <{EMAIL_FROM}>"
        msg['To'] = destinatario
        msg['cc'] = destinatario_admin
        msg['Subject'] = '✨ ¡Cita Confirmada! - Editar empresa'

        duracion_legible = f"{duration_minutes // 60}h {duration_minutes % 60}m"
        
        html_body = fhtml_body = f"""
<html>
    <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f1f5f9; padding: 40px 10px; margin: 0;">
        <div style="background-color: white; padding: 0; border-radius: 24px; max-width: 550px; margin: auto; border: 1px solid #e2e8f0; overflow: hidden; shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);">
            
            <div style="background-color: #0ea5e9; padding: 40px 20px; text-align: center;">
                <div style="background-color: rgba(255,255,255,0.2); width: 60px; height: 60px; border-radius: 15px; margin: 0 auto 15px; display: block;">
                    <span style="font-size: 30px; line-height: 60px;">✨</span>
                </div>
                <h2 style="color: white; margin: 0; font-size: 26px; font-weight: 800; letter-spacing: -0.5px;">¡Cita Confirmada!</h2>
            </div>

            <div style="padding: 40px 30px;">
                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin-top: 0;">
                    Hola <b style="color: #0f172a;">{nombre}</b>,<br>
                    Tu espacio ha sido reservado con éxito en <b style="color: #0ea5e9;">Editar empresa</b>. Aquí tienes los detalles de tu cita:
                </p>

                <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px; padding: 25px; margin: 30px 0;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding-bottom: 15px;">
                                <span style="font-size: 13px; color: #64748b; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">📅 Fecha y Hora</span><br>
                                <span style="font-size: 16px; color: #1e293b; font-weight: 600;">{fecha} — {hora}</span>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding-bottom: 15px;">
                                <span style="font-size: 13px; color: #64748b; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">💅 Servicio</span><br>
                                <span style="font-size: 16px; color: #1e293b; font-weight: 600;">{tipo_una}</span> 
                                <span style="font-size: 14px; color: #94a3b8;">({duracion_legible})</span>
                            </td>
                        </tr>
                    </table>
                </div>

                <div style="text-align: center; margin-bottom: 20px;">
                    <a href="{calendar_link}" style="display: inline-block; background-color: #0ea5e9; color: white; padding: 14px 28px; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 14px; box-shadow: 0 4px 6px -1px rgba(14, 165, 233, 0.3);">
                        Añadir a Google Calendar
                    </a>
                </div>
                
                <p style="color: #94a3b8; font-size: 13px; text-align: center; margin-top: 30px;">
                    ¿Necesitas cambios? Contacta directamente con el establecimiento.
                </p>
            </div>

            <div style="background-color: #f8fafc; padding: 30px; text-align: center; border-top: 1px solid #e2e8f0;">
                <p style="color: #64748b; font-size: 14px; margin-bottom: 8px; font-weight: 500;">
                    Gracias por utilizar <b style="color: #0ea5e9;">AgendApp</b>
                </p>
                <p style="color: #94a3b8; font-size: 12px; margin-bottom: 15px;">
                    Reserva tu espacio fácil e inteligente con AgendApp
                </p>
                <a href="https://agendapp.co" style="color: #0ea5e9; text-decoration: none; font-size: 13px; font-weight: bold; border: 1px solid #0ea5e9; padding: 6px 12px; border-radius: 8px;">
                    visitar agendapp.co
                </a>
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