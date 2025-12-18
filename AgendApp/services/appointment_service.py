from datetime import datetime
from utils.reservations import (
    cargar_reservas, 
    guardar_reservas, 
    DURACION_SERVICIOS, 
    format_google_calendar_datetime, 
    enviar_correo_confirmacion,
    HORAS_DISPONIBLES
)

def obtener_horas_disponibles(reservas, fecha_a_mostrar):
    """Calcula horas libres filtrando las ocupadas y las pasadas."""
    from utils.reservations import get_horas_ocupadas_por_superposicion
    
    horas_ocupadas = get_horas_ocupadas_por_superposicion(reservas, fecha_a_mostrar)
    ahora = datetime.now()
    horas_libres = []

    for h in HORAS_DISPONIBLES:
        h = h.strip()
        if h in horas_ocupadas:
            continue
            
        # Evitar citas en el pasado si es hoy
        try:
            hora_cita_dt = datetime.strptime(f"{fecha_a_mostrar} {h}", "%Y-%m-%d %H:%M")
            if hora_cita_dt > ahora:
                horas_libres.append(h)
        except:
            continue
            
    return horas_libres

def crear_cita(data, host_url):
    # 1. CARGAR LO EXISTENTE
    reservas = cargar_reservas()
    
    fecha = data.get('date')
    hora = data.get('hora')
    servicio = data.get('tipo_una')
    duracion = DURACION_SERVICIOS.get(servicio, 60)
    
    # 2. CREAR NUEVA CITA
    timestamp = str(datetime.now().timestamp()).replace('.', '')
    nueva_cita = {
        'nombre': data.get('nombre'),
        'email': data.get('email'),
        'telefono': data.get('telefono'),
        'date': fecha,
        'hora': hora,
        'tipo_una': servicio,
        'duracion': duracion,
        'notes': data.get('notes', ''),
        'timestamp': timestamp
    }
    
    # 3. AGREGAR A LA LISTA (Sin borrar lo anterior)
    reservas.append(nueva_cita)
    
    # 4. GUARDAR TODO
    guardar_reservas(reservas)
    
    # 5. ENVIAR NOTIFICACIÓN
    start, end = format_google_calendar_datetime(fecha, hora, duracion)
    cal_link = f"https://www.google.com/calendar/render?action=TEMPLATE&text=Cita+Nails&dates={start}/{end}"
    can_link = f"{host_url}cancelar/{timestamp}"
    
    enviar_correo_confirmacion(nueva_cita, cal_link, can_link)
    
    return {"status": "success"}