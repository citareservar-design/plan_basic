import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime

# Importamos los servicios y utilidades necesarios
from services.appointment_service import (
    crear_cita, 
    obtener_horas_disponibles, 
    cancelar_cita_por_id, 
    reagendar_cita_por_id,
    obtener_horas_libres_reagendar
)
from utils.reservations import cargar_reservas, guardar_reservas

# Definimos el Blueprint
appointment_bp = Blueprint('appointment', __name__)

# --- FUNCIÓN DE UTILIDAD PARA VALIDAR DOMINGOS ---
def es_domingo(fecha_str):
    """Retorna True si la fecha (YYYY-MM-DD) es domingo (6 en Python)."""
    try:
        if not fecha_str:
            return False
        fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
        return fecha_obj.weekday() == 6
    except ValueError:
        return False

@appointment_bp.route('/')
def index():
    return redirect(url_for('appointment.form'))

@appointment_bp.route('/form', methods=['GET', 'POST'])
def form():
    hoy = datetime.now().strftime("%Y-%m-%d")
    
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            
            # VALIDACIÓN: Bloqueo de domingos al crear cita
            if es_domingo(data.get('date')):
                flash("Lo sentimos, los domingos no estamos disponibles para citas.", "danger")
                return redirect(url_for('appointment.form'))

            resultado = crear_cita(data, request.host_url) 

            if "error" in resultado:
                flash(f"{resultado['error']}", "danger")
                return redirect(url_for('appointment.form'))

            return redirect(url_for('appointment.reserva_exitosa'))

        except Exception as e:
            flash(f"Error al procesar la reserva: {str(e)}", "danger")
            return redirect(url_for('appointment.form'))

    fecha_a_mostrar = request.args.get('date', hoy)
    
    # VALIDACIÓN: Si el usuario selecciona domingo en el selector de fecha
    if es_domingo(fecha_a_mostrar):
        flash("📅 Has seleccionado un domingo. Por favor, elige otro día de la semana.", "warning")
        horas_libres = [] # No mostramos horas si es domingo
    else:
        reservas = cargar_reservas()
        horas_libres = obtener_horas_disponibles(reservas, fecha_a_mostrar)

    form_data = {
        'nombre': request.args.get('nombre', ''),
        'email': request.args.get('email', ''),
        'notas': request.args.get('notes', ''),
        'tipo_una': request.args.get('tipo_una', ''),
        'telefono': request.args.get('telefono', ''),
        'hora_previa': request.args.get('hora', '')
    }

    return render_template(
        'form.html',
        hoy=hoy,
        horas_libres=horas_libres,
        fecha_seleccionada=fecha_a_mostrar,
        form_data=form_data
    )

@appointment_bp.route('/citas', methods=['GET', 'POST'])
def citas():
    email_buscado = request.form.get('email_cliente') or request.args.get('email_cliente')
    
    citas_cliente = []
    if email_buscado:
        reservas = cargar_reservas()
        citas_cliente = [r for r in reservas if r.get('email') == email_buscado]
        # Ordenamos las citas por fecha y hora
        citas_cliente.sort(key=lambda x: (x['date'], x['hora']))
    
    return render_template('citas.html', 
                            citas_cliente=citas_cliente, 
                            email_buscado=email_buscado)

@appointment_bp.route('/reserva_exitosa')
def reserva_exitosa(): 
    return render_template('reserva_exitosa.html')

# --- NUEVAS RUTAS API PARA FUNCIONES MÓVILES ---

@appointment_bp.route('/api/horas-disponibles/<fecha>')
def api_horas_disponibles(fecha):
    # VALIDACIÓN: Bloqueo de domingos en la API de horas
    if es_domingo(fecha):
        return jsonify([]) # Retorna lista vacía si es domingo
        
    horas = obtener_horas_libres_reagendar(fecha)
    return jsonify(horas)

@appointment_bp.route('/api/reagendar/<timestamp>', methods=['POST'])
def api_reagendar(timestamp):
    data = request.get_json()
    nueva_fecha = data.get('date')
    nueva_hora = data.get('hora')
    
    # VALIDACIÓN: Bloqueo de domingos al reagendar
    if es_domingo(nueva_fecha):
        return jsonify({"status": "error", "message": "No se puede reagendar para un domingo."}), 400
    
    if not nueva_fecha or not nueva_hora:
        return jsonify({"status": "error", "message": "Datos incompletos"}), 400
        
    resultado = reagendar_cita_por_id(timestamp, nueva_fecha, nueva_hora)
    return jsonify(resultado)

@appointment_bp.route('/api/cancelar/<timestamp>', methods=['POST'])
def api_cancelar(timestamp):
    resultado = cancelar_cita_por_id(timestamp)
    return jsonify(resultado)

@appointment_bp.route('/cancelar/<timestamp>', methods=['GET', 'POST'])
def cancelar_cita(timestamp):
    reservas = cargar_reservas()
    reserva_a_borrar = next((r for r in reservas if r.get('timestamp') == timestamp), None)
    
    if reserva_a_borrar:
        cancelar_cita_por_id(timestamp)
        if request.referrer and 'admin' in request.referrer:
            return redirect(url_for('admin.agenda'))
        
        return redirect(url_for('appointment.citas', email_cliente=reserva_a_borrar.get('email')))

    return redirect(url_for('appointment.index'))