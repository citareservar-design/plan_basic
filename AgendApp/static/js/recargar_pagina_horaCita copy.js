function actualizarHoras() {
    const fecha = document.getElementById('date').value;
    const nombre = document.getElementById('nombre').value;
    const email = document.getElementById('email').value;
    const telefono = document.getElementById('telefono').value;
    const tipo_una = document.getElementById('tipo_una').value;
    const notas = document.getElementById('notes').value;

    // Redirigimos al formulario pasando todos los datos actuales
    // Importante: La ruta sigue siendo /form porque es la URL del navegador
    let url = `/form?date=${fecha}`;
    
    if (nombre) url += `&nombre=${encodeURIComponent(nombre)}`;
    if (email) url += `&email=${encodeURIComponent(email)}`;
    if (telefono) url += `&telefono=${encodeURIComponent(telefono)}`;
    if (tipo_una) url += `&tipo_una=${encodeURIComponent(tipo_una)}`;
    if (notas) url += `&notes=${encodeURIComponent(notas)}`;

    window.location.href = url;
}