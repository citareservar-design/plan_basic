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

function validarYEnviar(input) {
    if (!input.value) return;

    // Crear la fecha (añadimos la hora para evitar desfases de zona horaria)
    const fechaSeleccionada = new Date(input.value + 'T00:00:00');
    const diaSemana = fechaSeleccionada.getDay(); // 0 es Domingo

    if (diaSemana === 0) {
        // Es Domingo: Bloqueamos
        alert("Lo sentimos, los domingos no abrimos. Por favor selecciona otro día.");
        input.value = ""; // Limpiamos el selector
    } else {
        // Es un día válido: Ejecutamos tu lógica original
        marcarCambiandoFecha();
        input.form.method = 'get';
        input.form.submit();
    }
}
