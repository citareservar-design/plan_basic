function actualizarHoras() {
    const fecha = document.getElementById('date').value;
    // Capturamos los otros campos para no perder lo que el usuario ya escribió
    const urlParams = new URLSearchParams(window.location.search);
    
    // Redirigir a la misma página pero con la nueva fecha
    window.location.href = window.location.pathname + '?date=' + fecha;
}