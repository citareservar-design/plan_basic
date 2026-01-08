
console.log("form_intro.js cargadooooooo correctamente");

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
    // 1. Identificamos los elementos (He ajustado los nombres según tu HTML)
    const inputFecha = document.getElementById('date'); // O 'fecha'
    const selectServicio = document.getElementById('servicio');
    const selectHoras = document.getElementById('select-horas');

    if (!inputFecha || !selectServicio || !selectHoras) return;

    const fechaVal = inputFecha.value;
    const servicioVal = selectServicio.value;

    // 2. LIMPIEZA INMEDIATA (Esto borra las horas AM apenas cambias algo)
    selectHoras.innerHTML = '<option value="" disabled selected>Cargando disponibilidad...</option>';

    if (!fechaVal || !servicioVal) {
        if (!servicioVal) {
            selectHoras.innerHTML = '<option value="" disabled selected>Selecciona un servicio primero</option>';
        }
        return;
    }

    try {
        const url = `/api/horas-disponibles/${fechaVal}?servicio=${encodeURIComponent(servicioVal.toLowerCase())}`;
        const response = await fetch(url);
        const horas = await response.json();

        // 3. SEGUNDA LIMPIEZA para quitar el "Cargando..."
        selectHoras.innerHTML = ''; 

if (horas.length === 0) {
            selectHoras.innerHTML = '<option value="" disabled selected>Sin disponibilidad</option>';
            
            // Mensaje estilo AgendApp (Azul y Blanco)
            Swal.fire({
                title: '<span style="color: #0f172a; font-weight: 900;">¡SIN TURNOS!</span>',
                text: 'No hay horarios disponibles para este servicio en la fecha seleccionada.',
                icon: 'info',
                iconColor: '#0ea5e9', // El azul de tu logo
                confirmButtonText: 'ENTENDIDO',
                confirmButtonColor: '#0ea5e9',
                background: '#ffffff',
                customClass: {
                    popup: 'rounded-3xl', // Bordes redondeados como tus tarjetas
                    confirmButton: 'rounded-xl font-bold px-8 uppercase text-xs tracking-widest'
                }
            });
        } else {
            // Opción por defecto
            const placeholder = document.createElement('option');
            placeholder.value = "";
            placeholder.disabled = true;
            placeholder.selected = true;
            placeholder.textContent = "Selecciona una hora...";
            selectHoras.appendChild(placeholder);

            // 4. INSERTAMOS LAS HORAS FILTRADAS
            horas.forEach(h => {
                const opt = document.createElement('option');
                opt.value = h.valor;
                opt.textContent = h.texto;
                opt.className = "bg-white text-slate-900 font-semibold";
                selectHoras.appendChild(opt);
            });
        }
    } catch (error) {
        console.error("Error:", error);
        selectHoras.innerHTML = '<option value="" disabled selected>Error al cargar</option>';
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


// Ejecutar la carga de horas si ya hay valores al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    const inputFecha = document.getElementById('date');
    const selectServicio = document.getElementById('servicio');
    
    if (inputFecha.value && selectServicio.value) {
        validarYEnviar();
    }
});