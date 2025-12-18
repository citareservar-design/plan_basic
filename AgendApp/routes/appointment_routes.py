import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime

# Importamos los servicios y utilidades necesarios
from services.appointment_service import crear_cita, obtener_horas_disponibles
from utils.reservations import cargar_reservas, guardar_reservas

# Definimos el Blueprint
appointment_bp = Blueprint('appointment', __name__)

@appointment_bp.route('/')
def index():
    return redirect(url_for('appointment.form'))

@appointment_bp.route('/form', methods=['GET', 'POST'])
def form():
    hoy = datetime.now().strftime("%Y-%m-%d")
    
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            resultado = crear_cita(data, request.host_url) 

            if "error" in resultado:
                flash(f"❌ {resultado['error']}", "danger")
                return redirect(url_for('appointment.form'))

            return redirect(url_for('appointment.reserva_exitosa'))

        except Exception as e:
            flash(f"❌ Error al procesar la reserva: {str(e)}", "danger")
            return redirect(url_for('appointment.form'))

    fecha_a_mostrar = request.args.get('date', hoy)
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

@appointment_bp.route('/cancelar/<timestamp>', methods=['GET', 'POST']) # Agregamos methods
def cancelar_cita(timestamp):
    reservas = cargar_reservas()
    reserva_a_borrar = next((r for r in reservas if r.get('timestamp') == timestamp), None)
    
    if reserva_a_borrar:
        email_cliente = reserva_a_borrar.get('email')
        nuevas_reservas = [r for r in reservas if r.get('timestamp') != timestamp]
        guardar_reservas(nuevas_reservas)
        
        referer = request.referrer
        
        # Si venías del panel de admin, te refresca ahí mismo
        if referer and '/admin/agenda' in referer:
            return redirect(url_for('admin.agenda'))
        
        # Si venías de la vista de cliente
        return redirect(url_for('appointment.citas', email_cliente=email_cliente))

    return redirect(url_for('appointment.index'))


@appointment_bp.route('/reserva_exitosa')
def reserva_exitosa(): 
    return render_template('reserva_exitosa.html')

@appointment_bp.route('/cancelacion_exitosa')
def cancelacion_exitosa(): 
    return render_template('cancelacion_exitosa.html')

@appointment_bp.route('/citas', methods=['GET', 'POST'])
def citas():
    email_buscado = request.form.get('email_cliente') or request.args.get('email_cliente')
    
    citas_cliente = []
    if email_buscado:
        reservas = cargar_reservas()
        citas_cliente = [r for r in reservas if r.get('email') == email_buscado]
    
    return render_template('citas.html', 
                            citas_cliente=citas_cliente, 
                            email_buscado=email_buscado)