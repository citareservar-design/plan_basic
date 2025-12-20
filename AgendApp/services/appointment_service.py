from datetime import datetime
from utils.reservations import (
    cargar_reservas, 
    guardar_reservas, 
    DURACION_SERVICIOS, 
    format_google_calendar_datetime, 
    enviar_correo_confirmacion,
    enviar_correo_reagendacion,
    enviar_correo_cancelacion, # Nueva importación
    HORAS_DISPONIBLES
)

def obtener_horas_disponibles(reservas, fecha_a_mostrar):
    from utils.reservations import get_horas_ocupadas_por_superposicion
    horas_ocupadas = get_horas_ocupadas_por_superposicion(reservas, fecha_a_mostrar)
    ahora = datetime.now()
    horas_libres = []
    for h in HORAS_DISPONIBLES:
        h = h.strip()
        if h in horas_ocupadas: continue
        try:
            if datetime.strptime(f"{fecha_a_mostrar} {h}", "%Y-%m-%d %H:%M") > ahora:
                horas_libres.append(h)
        except: continue
    return horas_libres

def obtener_horas_libres_reagendar(fecha):
    return obtener_horas_disponibles(cargar_reservas(), fecha)

def crear_cita(data, host_url):
    reservas = cargar_reservas()
    
    # Extraer variables necesarias del diccionario 'data'
    fecha = data.get('date')
    hora = data.get('hora')
    servicio = data.get('tipo_una')
    duracion = DURACION_SERVICIOS.get(servicio, 60)
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
    
    reservas.append(nueva_cita)
    guardar_reservas(reservas)
    
    # Generar links
    start, end = format_google_calendar_datetime(fecha, hora, duracion)
    cal_link = f"https://www.google.com/calendar/render?action=TEMPLATE&text=Cita+Nails&dates={start}/{end}"
    citas_link = f"{host_url}citas?email_cliente={nueva_cita['email']}"
    
    # Enviar correo (Asegúrate que reservations.py acepte 3 argumentos)
    enviar_correo_confirmacion(nueva_cita, cal_link, citas_link)
    
    return {"status": "success"}

def cancelar_cita_por_id(id_cita):
    """Busca la cita, envía correo de cancelación y luego la elimina."""
    reservas = cargar_reservas()
    cita_a_cancelar = next((r for r in reservas if r.get('timestamp') == id_cita), None)
    
    if cita_a_cancelar:
        # 1. Enviar correo antes de borrarla de la lista
        enviar_correo_cancelacion(cita_a_cancelar)
        
        # 2. Filtrar la lista para eliminarla
        nuevas_reservas = [r for r in reservas if r.get('timestamp') != id_cita]
        guardar_reservas(nuevas_reservas)
        return {"status": "success", "message": "Cita cancelada y notificada"}
    
    return {"status": "error", "message": "No se encontró la cita"}

def reagendar_cita_por_id(id_cita, nueva_fecha, nueva_hora):
    reservas = cargar_reservas()
    cita_modificada = None
    for cita in reservas:
        if cita.get('timestamp') == id_cita:
            cita['date'], cita['hora'] = nueva_fecha, nueva_hora
            cita_modificada = cita
            break

    if cita_modificada:
        guardar_reservas(reservas)
        start, end = format_google_calendar_datetime(nueva_fecha, nueva_hora, cita_modificada.get('duracion', 60))
        nuevo_cal_link = f"https://www.google.com/calendar/render?action=TEMPLATE&text=Cita+Reagendada&dates={start}/{end}"
        
        # LLAMADA REVERTIDA: Solo pasamos reserva y el link de calendario
        enviar_correo_reagendacion(cita_modificada, nuevo_cal_link) 
        
        return {"status": "success", "message": "Cita reagendada"}