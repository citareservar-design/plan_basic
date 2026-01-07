        const progressBar = document.getElementById('progress-bar');
        const counter = document.getElementById('counter');
        const intro = document.getElementById('intro-screen');
        const main = document.getElementById('main-content');

        function marcarCambiandoFecha() {
            sessionStorage.setItem('saltarIntro', 'true');
        }

        window.onload = function() {
            if (sessionStorage.getItem('saltarIntro') === 'true') {
                intro.style.display = 'none';
                main.classList.add('show-content');
                sessionStorage.removeItem('saltarIntro');
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
                        intro.classList.add('fade-out');
                        setTimeout(() => {
                            intro.style.display = 'none';
                            main.classList.add('show-content');
                        }, 800);
                    }, 400);
                }
                progressBar.style.width = progress + '%';
                counter.innerText = progress + '%';
            }, 150);
        }

async function validarYEnviar(input) {
    if (!input.value) return;

    // 1. Validación local rápida de domingos
    const fechaSeleccionada = new Date(input.value + 'T00:00:00');
    if (fechaSeleccionada.getDay() === 0) {
        alert("📅 Los domingos no estamos disponibles. Por favor, elige otro día.");
        input.value = "";
        return;
    }

    // 2. Referencia al select de horas
    const selectHoras = document.querySelector('select[name="hora"]');
    
    // Feedback visual: Limpiamos y mostramos que está cargando
    selectHoras.innerHTML = '<option value="" disabled selected>Cargando disponibilidad...</option>';

    try {
        // 3. Llamada a tu ruta API (La que ya tienes en Python)
        const response = await fetch(`/api/horas-disponibles/${input.value}`);
        const horas = await response.json();

        // 4. Limpiar el select y llenarlo con los nuevos datos
        selectHoras.innerHTML = ''; // Limpiamos el "Cargando..."

        if (horas.length === 0) {
            selectHoras.innerHTML = '<option value="" disabled selected>No hay citas disponibles</option>';
        } else {
            // Añadimos la opción por defecto
            const defaultOpt = document.createElement('option');
            defaultOpt.value = "";
            defaultOpt.disabled = true;
            defaultOpt.selected = true;
            defaultOpt.textContent = "Selecciona una hora...";
            selectHoras.appendChild(defaultOpt);

            // Llenamos con las horas que trajo la API
            horas.forEach(h => {
                const opt = document.createElement('option');
                opt.value = h.valor;
                opt.textContent = h.texto;
                opt.className = "bg-white text-slate-900 font-semibold";
                selectHoras.appendChild(opt);
            });
        }
    } catch (error) {
        console.error("Error cargando horas:", error);
        selectHoras.innerHTML = '<option value="" disabled selected>Error al cargar horas</option>';
    }
}