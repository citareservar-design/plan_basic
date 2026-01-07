from datetime import datetime, timedelta
from utils.reservations import (
    cargar_reservas, 
    guardar_reservas, 
    DURACION_SERVICIOS, 
    format_google_calendar_datetime, 
    enviar_correo_confirmacion,
    enviar_correo_reagendacion,
    enviar_correo_cancelacion, # Nueva importación
    HORAS_DISPONIBLES,
    formatear_hora_12h,
    cargar_config, get_horas_ocupadas_por_superposicion
)


from datetime import datetime, timedelta

def obtener_horas_disponibles(reservas, fecha_a_mostrar, duracion_servicio=60):
    from utils.reservations import get_horas_ocupadas_por_superposicion, cargar_config
    
    config = cargar_config()
    horas_base = config.get("horarios_base", [])
    almuerzo = config.get('almuerzo', {"inicio": "12:00", "fin": "14:00"})
    hora_cierre_str = config.get('hora_cierre', '20:00')
    
    horas_ocupadas = get_horas_ocupadas_por_superposicion(reservas, fecha_a_mostrar)
    ahora = datetime.now()
    horas_libres = []

    # Convertimos hora de cierre a objeto time para comparar
    dt_cierre = datetime.strptime(hora_cierre_str, "%H:%M").time()

    for h in horas_base:
        h = h.strip()
        
        # 1. Filtro Ocupado (Citas ya existentes)
        if h in horas_ocupadas:
            continue
        
        try:
            # Convertimos la hora actual del ciclo a objeto datetime para cálculos
            hora_inicio_dt = datetime.strptime(h, "%H:%M")
            # Sumamos la duración real del servicio (ej: 120 min)
            hora_fin_dt = hora_inicio_dt + timedelta(minutes=int(duracion_servicio))
            
            # --- NUEVA LÓGICA DE COLISIÓN DE ALMUERZO ---
            # Definimos los límites del almuerzo
            almuerzo_inicio = datetime.strptime(almuerzo['inicio'], "%H:%M")
            almuerzo_fin = datetime.strptime(almuerzo['fin'], "%H:%M")

            # REGLA: Si la cita empieza antes de que termine el almuerzo 
            # Y termina después de que el almuerzo empiece -> HAY CRUCE
            if hora_inicio_dt < almuerzo_fin and hora_fin_dt > almuerzo_inicio:
                continue

            # --- FILTRO DE CIERRE ---
            # Si termina después del cierre (ej: 18:01 cerrando a las 18:00) -> BLOQUEAR
            if hora_fin_dt.time() > dt_cierre:
                continue

            # --- FILTRO DE HORAS PASADAS (Solo si es HOY) ---
            fecha_hoy = ahora.strftime("%Y-%m-%d")
            if fecha_a_mostrar == fecha_hoy:
                # Si la hora de inicio es menor a la hora actual del servidor -> BLOQUEAR
                if hora_inicio_dt.time() < ahora.time():
                    continue

# Creamos el texto en formato 12 horas para el cliente
            # %I: hora (01-12), %M: minutos, %p: AM/PM
            hora_12h = hora_inicio_dt.strftime("%I:%M %p")

            # Guardamos: 
            # 'valor' -> "14:00" (Para que el servidor lo entienda)
            # 'texto' -> "02:00 PM" (Para que el cliente lo vea bonito)
            horas_libres.append({
                'valor': h, 
                'texto': hora_12h
            })
            
        except Exception as e:
            print(f"Error procesando la hora {h}: {e}")
            continue
            
    return horas_libres

def obtener_horas_libres_reagendar(fecha):
    return obtener_horas_disponibles(cargar_reservas(), fecha)

def crear_cita(data, host_url):
    # 1. Cargamos las reservas y la configuración actual
    from utils.reservations import cargar_reservas, guardar_reservas, cargar_config
    
    reservas = cargar_reservas()
    config = cargar_config()
    
    # 2. Obtenemos el diccionario de servicios del JSON
    # Si no existe en el JSON, usamos un diccionario vacío {}
    servicios_config = config.get('servicios', {})
    
    # Extraer variables necesarias del diccionario 'data'
    fecha = data.get('date')
    hora = data.get('hora')
    servicio = data.get('tipo_una')
    
    # 3. CAMBIO CLAVE: Buscamos la duración en el JSON. 
    # Si el servicio no existe allí, le damos 60 minutos por defecto.
    duracion = servicios_config.get(servicio, 60)
    
    timestamp = str(datetime.now().timestamp()).replace('.', '')

    nueva_cita = {
        'nombre': data.get('nombre'), 
        'email': data.get('email'), 
        'telefono': data.get('telefono'),
        'date': fecha, 
        'hora': hora, 
        'tipo_una': servicio, 
        'duracion': duracion, # Ahora esta duración es la del JSON
        'notes': data.get('notes', ''), 
        'timestamp': timestamp
    }
    
    reservas.append(nueva_cita)
    guardar_reservas(reservas)
    
    # Generar links
    start, end = format_google_calendar_datetime(fecha, hora, duracion)
    cal_link = f"https://www.google.com/calendar/render?action=TEMPLATE&text=Cita+Nails&dates={start}/{end}"
    citas_link = f"{host_url}citas?email_cliente={nueva_cita['email']}"
    
    # Enviar correo
    enviar_correo_confirmacion(nueva_cita, cal_link, citas_link)
    
    return {"status": "success"}

def cancelar_cita_por_id(id_cita):
    """Busca la cita, envía correo de cancelación y luego la elimina."""
    reservas = cargar_reservas()
    cita_a_cancelar = next((r for r in reservas if r.get('timestamp') == id_cita), None)
    
    if cita_a_cancelar:
        # 1. Enviar correo antes de borrarla de la list
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