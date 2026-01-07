console.log("Citas.js cargado");


// 1. CANCELAR CITA
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
      // --- DISPARAR LOADER DE AGENDAPP ---
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
            // Éxito: Barra al 100%
            if (progressBar) progressBar.style.width = "100%";
            if (loaderMsg) loaderMsg.innerText = "Cita eliminada correctamente.";
            
            setTimeout(() => {
              location.reload();
            }, 1000);
          } else {
            // Si hay error, ocultamos loader y mostramos el error
            if (loader) loader.style.display = 'none';
            Swal.fire('Error', data.message || 'No se pudo cancelar', 'error');
          }
        })
        .catch(err => {
          if (loader) loader.style.display = 'none';
          Swal.fire('Error', 'Error de conexión con el servidor', 'error');
        });
    }
  });
};













// 2. REAGENDAR CITA
const prepararReagendar = (timestamp) => {
  const hoy = new Date().toISOString().split('T')[0];
  
  Swal.fire({
    title: 'Reagendar Cita',
    html: `
      <div class="flex flex-col gap-4 text-left">
        <div>
          <label class="text-[10px] font-bold uppercase text-slate-400">Nueva Fecha</label>
          <input type="date" id="new_date" min="${hoy}" class="w-full px-4 py-2 rounded-xl border border-slate-200 outline-none focus:border-brand-500" value="${hoy}">
        </div>
        <div>
          <label class="text-[10px] font-bold uppercase text-slate-400">Hora Disponible</label>
          <select id="new_hour" class="w-full px-4 py-2 rounded-xl border border-slate-200 outline-none focus:border-brand-500">
            <option value="">Seleccione una fecha primero</option>
          </select>
        </div>
      </div>
    `,
    showCancelButton: true,
    confirmButtonText: 'Actualizar',
    confirmButtonColor: '#0ea5e9',
    didOpen: () => {
      const dateInput = document.getElementById('new_date');
      const hourSelect = document.getElementById('new_hour');
      
      const cargarHoras = (fecha) => {
        const fechaObj = new Date(fecha + 'T00:00:00');
        if (fechaObj.getDay() === 0) {
            hourSelect.innerHTML = '<option value="">Domingos Cerrado</option>';
            return;
        }

        hourSelect.innerHTML = '<option value="">Cargando...</option>';
        fetch(`/api/horas-disponibles/${fecha}`)
          .then(res => res.json())
          .then(horas => {
            if (horas && horas.length > 0) {
              hourSelect.innerHTML = horas.map(h => 
                `<option value="${h.valor}">${h.texto}</option>`
              ).join('');
            } else {
              hourSelect.innerHTML = '<option value="">Sin turnos libres</option>';
            }
          })
          .catch(err => {
            hourSelect.innerHTML = '<option value="">Error al cargar</option>';
          });
      };

      dateInput.addEventListener('change', (e) => cargarHoras(e.target.value));
      cargarHoras(dateInput.value);
    },
    preConfirm: () => {
      const date = document.getElementById('new_date').value;
      const hora = document.getElementById('new_hour').value;
      if (!hora) return Swal.showValidationMessage('Debes elegir una hora');
      return { date, hora };
    }
  }).then((result) => {
    if (result.isConfirmed) {
      // --- AQUÍ DISPARAMOS TU ANIMACIÓN ---
      const loader = document.getElementById('loader-agendapp');
      const progressBar = document.getElementById('progress-bar');
      const loaderMsg = document.getElementById('loader-msg');

      if (loader) loader.style.display = 'flex';
      if (progressBar) progressBar.style.width = "40%";
      if (loaderMsg) loaderMsg.innerText = "Validando disponibilidad...";

      fetch(`/api/reagendar/${timestamp}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(result.value)
      })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
            if (progressBar) progressBar.style.width = "100%";
            if (loaderMsg) loaderMsg.innerText = "¡Cita reprogramada con éxito!";
            
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            if (loader) loader.style.display = 'none';
            Swal.fire('Error', data.message, 'error');
        }
      })
      .catch(err => {
        if (loader) loader.style.display = 'none';
        Swal.fire('Error', 'No se pudo conectar con el servidor', 'error');
      });
    }
  });
};