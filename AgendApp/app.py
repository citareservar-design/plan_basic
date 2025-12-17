import os
from flask import Flask, render_template, request, redirect, flash, url_for
from datetime import datetime
from services.appointment_service import obtener_horas_disponibles


# Utilidades que aún se usan en el GET
from utils.reservations import (
    cargar_reservas, guardar_reservas, normalizar_fecha, normalizar_hora,
    get_horas_ocupadas_por_superposicion, check_new_reservation_overlap,
    format_google_calendar_datetime, enviar_correo_confirmacion,
    DURACION_SERVICIOS, HORAS_DISPONIBLES
)


# Service de citas
from services.appointment_service import crear_cita

app = Flask(__name__)
app.secret_key = 'clave-secreta-segura-debes-cambiarla'


@app.route('/')
def index():
    if os.path.exists(os.path.join(app.root_path, 'templates', 'inicio.html')):
        return render_template('inicio.html')
    return redirect(url_for('form'))


@app.route('/form', methods=['GET', 'POST'])
def form():
    reservas = cargar_reservas()
    hoy = datetime.now().strftime("%Y-%m-%d")

    # -------- POST (crear cita) --------
    if request.method == 'POST':
        try:
            data = request.form.to_dict()
            resultado = crear_cita(data)

            if "error" in resultado:
                flash(f"❌ {resultado['error']}", "danger")
                return redirect(url_for('form'))

            return redirect(url_for('reserva_exitosa'))

        except Exception as e:
            flash(f"❌ Error al procesar la reserva: {str(e)}", "danger")
            return redirect(url_for('form'))

    # -------- GET (mostrar formulario) --------
    fecha_a_mostrar = request.args.get('date')
    if not fecha_a_mostrar:
        fecha_a_mostrar = datetime.now().strftime("%Y-%m-%d")
    
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


@app.route('/reserva_exitosa')
def reserva_exitosa():
    return render_template('reserva_exitosa.html')


@app.route('/cancelar/<timestamp>')
def cancelar_cita(timestamp):
    reservas = cargar_reservas()
    nuevas_reservas = [r for r in reservas if r.get('timestamp') != timestamp]

    if len(nuevas_reservas) < len(reservas):
        from utils import guardar_reservas
        guardar_reservas(nuevas_reservas)
        return redirect(url_for('cancelacion_exitosa'))

    flash("Cita no encontrada.", "warning")
    return redirect(url_for('index'))


@app.route('/cancelacion_exitosa')
def cancelacion_exitosa():
    return render_template('cancelacion_exitosa.html')


@app.route('/citas', methods=['GET', 'POST'])
def citas():
    reservas = cargar_reservas()
    citas_cliente = None
    email_buscado = None

    if request.method == 'POST':
        email_buscado = request.form.get('email_cliente', '').strip().lower()
        citas_cliente = [
            r for r in reservas if r.get('email', '').lower() == email_buscado
        ]

    return render_template(
        'citas.html',
        citas_cliente=citas_cliente,
        email_buscado=email_buscado
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
