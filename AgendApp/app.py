from flask import Flask
# Aquí es donde traemos los "guiadores" de las otras carpetas
from routes.appointment_routes import appointment_bp
from routes.admin_routes import admin_bp  # <--- ¡ESTA LÍNEA ES LA QUE FALTA!

app = Flask(__name__)
app.secret_key = 'clave-secreta-segura-debes-cambiarla'

# Registramos ambos guiadores
app.register_blueprint(appointment_bp)
app.register_blueprint(admin_bp, url_prefix='/admin')


@app.context_processor
def inject_config():
    from utils.reservations import cargar_config
    return dict(config=cargar_config())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    
    