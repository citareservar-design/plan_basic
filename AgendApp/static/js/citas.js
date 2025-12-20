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
            fetch(`/api/cancelar/${timestamp}`, { method: 'POST' })
              .then(res => res.json())
              .then(data => {
                Swal.fire('Eliminada', data.message, 'success').then(() => location.reload());
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
              hourSelect.innerHTML = '<option value="">Cargando...</option>';
              fetch(`/api/horas-disponibles/${fecha}`)
                .then(res => res.json())
                .then(horas => {
                  if (horas.length > 0) {
                    hourSelect.innerHTML = horas.map(h => `<option value="${h}">${h}</option>`).join('');
                  } else {
                    hourSelect.innerHTML = '<option value="">Sin turnos libres</option>';
                  }
                });
            };

            dateInput.addEventListener('change', (e) => cargarHoras(e.target.value));
            cargarHoras(dateInput.value); // Carga inicial para hoy
          },
          preConfirm: () => {
            const date = document.getElementById('new_date').value;
            const hora = document.getElementById('new_hour').value;
            if (!hora) return Swal.showValidationMessage('Debes elegir una hora');
            return { date, hora };
          }
        }).then((result) => {
          if (result.isConfirmed) {
            fetch(`/api/reagendar/${timestamp}`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(result.value)
            })
            .then(res => res.json())
            .then(data => {
              Swal.fire('Éxito', data.message, 'success').then(() => location.reload());
            });
          }
        });
      };