
console.log("form_intro.js cargado correctamente");

    // --- 1. ELEMENTOS DE LA INTRO ---
    const progressBar = document.getElementById('progress-bar');
    const counter = document.getElementById('counter');
    const intro = document.getElementById('intro-screen');
    const main = document.getElementById('main-content');

    // --- 2. ELEMENTOS DEL FORMULARIO ---
    // Usamos el selector por nombre para coincidir con tu HTML dinámico
    const selectServicio = document.querySelector('select[name="tipo_una"]'); 
    const inputFecha = document.getElementById('fecha');
    const selectHoras = document.querySelector('select[name="hora"]');

    // --- 3. LÓGICA DE LA INTRO (ORIGINAL) ---
    function marcarCambiandoFecha() {
        sessionStorage.setItem('saltarIntro', 'true');
    }

    window.onload = function() {
        if (sessionStorage.getItem('saltarIntro') === 'true') {
            if(intro) intro.style.display = 'none';
            if(main) main.classList.add('show-content');
            sessionStorage.removeItem('saltarIntro');
            
            // Si ya hay datos cargados (por ejemplo al volver atrás), actualizar horas
            if(inputFecha && inputFecha.value) {
                validarYEnviar();
            }
        } else {
            ejecutarIntro();
        }
    };

    function ejecutarIntro() {
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.floor(Math.random() * 15) + 10;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
                setTimeout(() => {
                    if(intro) intro.classList.add('fade-out');
                    setTimeout(() => {
                        if(intro) intro.style.display = 'none';
                        if(main) main.classList.add('show-content');
                    }, 800);
                }, 400);
            }
            if(progressBar) progressBar.style.width = progress + '%';
            if(counter) counter.innerText = progress + '%';
        }, 150);
    }

    // --- 4. LÓGICA DE VALIDACIÓN Y HORAS INTELIGENTES ---
   async function validarYEnviar() {
    // Definimos los elementos para asegurar que JS los encuentre siempre
    const inputFecha = document.getElementById('date');
    const selectServicio = document.getElementById('servicio');
    const selectHoras = document.getElementById('select-horas');

    // Validamos que los elementos existan en el HTML
    if (!inputFecha || !selectServicio || !selectHoras) {
        console.error("No se encontraron los elementos del formulario");
        return;
    }

    const fechaVal = inputFecha.value;
    const servicioVal = selectServicio.value;
    
    // 1. Guardamos la hora que el usuario tenía marcada antes de que la lista cambie
    const horaSeleccionadaAnteriormente = selectHoras.value; 

    // Si no hay fecha, no hacemos nada todavía
    if (!fechaVal) return;

    // Si hay fecha pero no servicio, pedimos elegir servicio
    if (!servicioVal) {
        selectHoras.innerHTML = '<option value="" disabled selected>Selecciona un servicio primero</option>';
        return;
    }

    // Mostramos un mensaje temporal mientras carga
    selectHoras.innerHTML = '<option value="" disabled selected>Cargando disponibilidad...</option>';

    try {
        // 2. Llamada a la API enviando fecha y servicio (en minúsculas)
        const url = `/api/horas-disponibles/${fechaVal}?servicio=${encodeURIComponent(servicioVal.toLowerCase())}`;
        const response = await fetch(url);
        const horas = await response.json();

        // 3. Limpiamos el selector para meter las nuevas opciones
        selectHoras.innerHTML = ''; 

        if (horas.length === 0) {
            selectHoras.innerHTML = '<option value="" disabled selected>No hay tiempo para este servicio</option>';
            alert("⚠️ No hay horarios disponibles para este servicio en la fecha seleccionada.");
        } else {
            // Creamos la opción por defecto
            const defaultOpt = document.createElement('option');
            defaultOpt.value = "";
            defaultOpt.disabled = true;
            defaultOpt.textContent = "Selecciona una hora...";
            selectHoras.appendChild(defaultOpt);

            let horaSigueSiendoValida = false;

            // 4. Llenamos el select con las horas que devolvió el Python
            horas.forEach(h => {
                const opt = document.createElement('option');
                opt.value = h.valor;
                opt.textContent = h.texto;
                
                // Si la hora de "hoy" coincide con la de "mañana", se mantiene seleccionada
                if (h.valor === horaSeleccionadaAnteriormente) {
                    opt.selected = true;
                    horaSigueSiendoValida = true;
                }
                selectHoras.appendChild(opt);
            });

            // 5. Si la hora vieja ya no existe (ej: era las 8am y hoy ya pasaron), reseteamos
            if (!horaSigueSiendoValida) {
                defaultOpt.selected = true;
                // Solo alertamos si el usuario ya había hecho una elección previa que ahora es inválida
                if (horaSeleccionadaAnteriormente !== "") {
                    alert("❌ La hora elegida ya no está disponible (puede ser por el cierre o porque ya pasó).");
                }
            }
        }
    } catch (error) {
        console.error("Error cargando disponibilidad:", error);
        selectHoras.innerHTML = '<option value="" disabled selected>Error al cargar horas</option>';
    }
}


async function confirmarReservaFinal() {
    const loader = document.getElementById('loader-agendapp');
    const btn = document.getElementById('btn-confirmar');
    const progressBar = document.getElementById('progress-bar');
    const loaderMsg = document.getElementById('loader-msg');
    
    // 1. Mostrar el loader
    if (loader) loader.style.display = 'flex';

    // 2. Deshabilitar botón para evitar doble reserva
    if (btn) {
        btn.disabled = true;
        btn.style.opacity = "0.5";
        btn.style.cursor = "not-allowed";
    }

    // 3. Obtener los datos del formulario (IDs validados)
    const datos = {
        nombre: document.getElementById('nombre')?.value,
        email: document.getElementById('email')?.value,
        telefono: document.getElementById('telefono')?.value,
        tipo_una: document.getElementById('servicio')?.value,
        date: document.getElementById('date')?.value,
        hora: document.getElementById('select-horas')?.value,
        notes: document.getElementById('notas')?.value
    };

    console.log("Datos capturados para enviar:", datos);

    // Animación visual de la barra mientras esperamos al servidor
    if (progressBar && loaderMsg) {
        setTimeout(() => { progressBar.style.width = "40%"; loaderMsg.innerText = "Validando disponibilidad..."; }, 200);
        setTimeout(() => { progressBar.style.width = "70%"; loaderMsg.innerText = "Asegurando tu cupo en AgendApp..."; }, 1000);
    }

    try {
        const response = await fetch('/confirmar-reserva', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(datos)
        });

        const contentType = response.headers.get("content-type");
        
        if (contentType && contentType.includes("application/json")) {
            const resultado = await response.json();
            
            if (response.ok) {
                // Éxito total
                if (progressBar) progressBar.style.width = "100%";
                if (loaderMsg) loaderMsg.innerText = "¡Cita confirmada! Redireccionando...";
                
                setTimeout(() => {
                    window.location.href = "/reserva_exitosa"; 
                }, 800);
            } else {
                throw new Error(resultado.message || "Error en el servidor");
            }
        } else {
            const errorHtml = await response.text();
            console.error("DEBUG DEL ERROR (HTML):", errorHtml);
            throw new Error("El servidor respondió con un error de página. Revisa la consola de Flask.");
        }

    } catch (error) {
        console.error("Error detallado:", error);
        alert("❌ No se pudo confirmar: " + error.message);
        
        // Resetear en caso de fallo
        if (loader) loader.style.display = 'none';
        if (btn) {
            btn.disabled = false;
            btn.style.opacity = "1";
            btn.style.cursor = "pointer";
        }
    }
}