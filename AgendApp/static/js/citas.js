console.log("Citas.js cargado");

// --- 1. CANCELAR CITA ---
const confirmarCancelacion = (timestamp) => {
    Swal.fire({
        title: '¿Eliminar cita?',
        text: "Esta acción no se puede deshacer.",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        confirmButtonText: 'Sí, cancelar',
        cancelButtonText: 'No, volver'
    }).then((result) => {
        if (result.isConfirmed) {
            const loader = document.getElementById('loader-agendapp');
            const progressBar = document.getElementById('progress-bar');
            const loaderMsg = document.getElementById('loader-msg');

            if (loader) loader.style.display = 'flex';
            if (progressBar) progressBar.style.width = "50%";
            if (loaderMsg) loaderMsg.innerText = "Cancelando tu cupo...";

            fetch(`/api/cancelar/${timestamp}`, { method: 'POST' })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success' || data.message.includes("éxito")) {
                        if (progressBar) progressBar.style.width = "100%";
                        if (loaderMsg) loaderMsg.innerText = "Cita eliminada correctamente.";
                        setTimeout(() => { location.reload(); }, 1000);
                    } else {
                        if (loader) loader.style.display = 'none';
                        Swal.fire('Error', data.message || 'No se pudo cancelar', 'error');
                    }
                })
                .catch(err => {
                    if (loader) loader.style.display = 'none';
                    Swal.fire('Error', 'Error de conexión', 'error');
                });
        }
    });
};

// --- 2. REAGENDAR CITA ---
function prepararReagendar(timestamp, servicio) {
    // 1. Limpieza profunda del texto
    let nombreServicio = servicio ? servicio.trim() : "";
    
    // Si el servicio viene vacío o es un error de Jinja, el log nos avisará
    console.log("--- DIAGNÓSTICO DE REAGENDADO ---");
    console.log("ID Cita:", timestamp);
    console.log("Servicio recibido del HTML:", nombreServicio);

    if (!nombreServicio || nombreServicio === "None") {
        console.error("ALERTA: El servicio llegó vacío desde la base de datos.");
        nombreServicio = "peinado 2horas"; // Respaldo
    }

    const hoy = new Date().toISOString().split('T')[0];

    Swal.fire({
        title: 'Reagendar Cita',
        html: `
            <div style="text-align: left;">
                <p style="font-size: 11px; background: #f1f5f9; padding: 5px; border-radius: 5px; color: #1e293b; font-weight: bold; margin-bottom: 10px; border-left: 4px solid #3b82f6;">
                    MODO: ${nombreServicio.toUpperCase()}
                </p>
                <label style="display: block; font-size: 10px; font-weight: bold; color: #64748b;">NUEVA FECHA</label>
                <input type="date" id="new_date" min="${hoy}" value="${hoy}" style="width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #e2e8f0; border-radius: 10px;">
                
                <label style="display: block; font-size: 10px; font-weight: bold; color: #64748b;">HORARIO DISPONIBLE</label>
                <select id="new_hour" style="width: 100%; padding: 10px; border: 1px solid #e2e8f0; border-radius: 10px;">
                    <option value="">Cargando horas...</option>
                </select>
            </div>
        `,
        didOpen: () => {
            const dateInput = document.getElementById('new_date');
            const hourSelect = document.getElementById('new_hour');

            const cargar = (fecha) => {
                hourSelect.innerHTML = '<option value="">Buscando bloques...</option>';
                // Aquí es donde se decide si son 120 o 180 min
                fetch(`/api/horas-disponibles/${fecha}?servicio=${encodeURIComponent(nombreServicio)}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data && data.length > 0) {
                            hourSelect.innerHTML = data.map(h => `<option value="${h.valor}">${h.texto}</option>`).join('');
                        } else {
                            hourSelect.innerHTML = `<option value="">No hay espacio suficiente para ${nombreServicio}</option>`;
                        }
                    });
            };
            dateInput.addEventListener('change', (e) => cargar(e.target.value));
            cargar(dateInput.value);
        }
    });
}