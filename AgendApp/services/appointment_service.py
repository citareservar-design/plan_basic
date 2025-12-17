from datetime import datetime

from utils.reservations import (
    cargar_reservas, guardar_reservas, normalizar_fecha, normalizar_hora,
    get_horas_ocupadas_por_superposicion, check_new_reservation_overlap,
    format_google_calendar_datetime, enviar_correo_confirmacion,
    DURACION_SERVICIOS, HORAS_DISPONIBLES,get_horas_ocupadas_por_superposicion
)


def crear_cita(data):
    reservas = cargar_reservas()

    nombre = data.get('nombre')
    email = data.get('email')
    telefono = data.get('telefono')
    tipo_una = data.get('tipo_una')
    date = data.get('date')
    hora = data.get('hora')
    notas = data.get('notes', '')

    if not all([nombre, email, tipo_una, date, hora]):
        return {"error": "Campos obligatorios faltantes"}

    fecha_normalizada = normalizar_fecha(date)
    hora_normalizada = normalizar_hora(hora)
    duration_minutes = DURACION_SERVICIOS.get(tipo_una, 60)

    if check_new_reservation_overlap(
        reservas, fecha_normalizada, hora_normalizada, duration_minutes
    ):
        return {"error": "Hora ocupada"}

    timestamp_cita = datetime.now().isoformat()

    nueva_reserva = {
        "nombre": nombre,
        "email": email,
        "telefono": telefono,
        "tipo_una": tipo_una,
        "notas": notas,
        "date": fecha_normalizada,
        "hora": hora_normalizada,
        "duracion": duration_minutes,
        "timestamp": timestamp_cita
    }

    reservas.append(nueva_reserva)
    guardar_reservas(reservas)

    start, end = format_google_calendar_datetime(
        fecha_normalizada, hora_normalizada, duration_minutes
    )

    calendar_link = (
        "https://calendar.google.com/calendar/render?"
        f"action=TEMPLATE&text=Cita%20Cocoa%20Nails&dates={start}/{end}"
    )

    enviar_correo_confirmacion(nueva_reserva, calendar_link, None)

    return {
        "success": True,
        "reserva": nueva_reserva,
        "calendar_link": calendar_link
    }



from datetime import datetime
from utils.reservations import (
    HORAS_DISPONIBLES,
    get_horas_ocupadas_por_superposicion
)

from datetime import datetime

def obtener_horas_disponibles(reservas, fecha):
    fecha = normalizar_fecha(fecha)
    now = datetime.now()
    
    fecha_hoy = now.date()
    fecha_seleccionada = datetime.strptime(fecha, "%Y-%m-%d").date()

    horas_reservadas = get_horas_ocupadas_por_superposicion(reservas, fecha)
    horas_libres = []

    for h in HORAS_DISPONIBLES:
        if h in horas_reservadas:
            continue

        # Convertimos la hora del JSON a un objeto datetime para comparar
        hora_cita_dt = datetime.strptime(f"{fecha} {h}", "%Y-%m-%d %H:%M")

        # LOGICA CLAVE:
        # Si el día es hoy, filtramos las que ya pasaron
        if fecha_seleccionada == fecha_hoy:
            if hora_cita_dt > now:
                horas_libres.append(h)
        # Si el día es mañana o futuro, mostramos TODO el JSON (8am, 9am, etc)
        elif fecha_seleccionada > fecha_hoy:
            horas_libres.append(h)

    return horas_libres