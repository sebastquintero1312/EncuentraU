(async function () {
  const usuario = await protegerPagina({ admin: true });
  if (!usuario) return;

  const ESTADOS_POSIBLES = ['activo', 'en_proceso', 'resuelto', 'cerrado', 'cancelado'];
  const cuerpoTabla = document.getElementById('cuerpo-tabla');

  async function cargar() {
    const resultado = await peticionGet('/admin/objetos?por_pagina=100');
    const reportes = resultado.datos.datos || [];
    cuerpoTabla.textContent = '';

    if (reportes.length === 0) {
      const fila = document.createElement('tr');
      const celda = crearElemento('td', 'No hay reportes.');
      celda.colSpan = 5;
      fila.appendChild(celda);
      cuerpoTabla.appendChild(fila);
      return;
    }

    reportes.forEach(reporte => {
      const fila = document.createElement('tr');
      fila.appendChild(crearElemento('td', reporte.nombre));

      const celdaTipo = crearElemento('td');
      celdaTipo.appendChild(crearBadge(reporte.tipo, 'badge-' + reporte.tipo));
      fila.appendChild(celdaTipo);

      fila.appendChild(crearElemento('td', reporte.usuario_nombre));

      const celdaEstado = crearElemento('td');
      const selector = document.createElement('select');
      ESTADOS_POSIBLES.forEach(estado => {
        const opcion = crearElemento('option', textoEstado(estado));
        opcion.value = estado;
        if (estado === reporte.estado) opcion.selected = true;
        selector.appendChild(opcion);
      });
      selector.addEventListener('change', async function () {
        const resultadoCambio = await peticionProtegida(`/admin/objetos/${reporte.id}/estado`, 'PUT', {
          estado: this.value,
        });
        if (!resultadoCambio.ok) {
          alert(resultadoCambio.datos.mensaje || 'No se pudo cambiar el estado');
          cargar();
        }
      });
      celdaEstado.appendChild(selector);
      fila.appendChild(celdaEstado);

      const celdaAcciones = crearElemento('td');
      const verDetalle = crearElemento('a', 'Ver detalle', 'btn btn-secondary btn-small');
      verDetalle.href = `detalle-objeto.html?id=${reporte.id}`;
      celdaAcciones.appendChild(verDetalle);
      fila.appendChild(celdaAcciones);

      cuerpoTabla.appendChild(fila);
    });
  }

  cargar();
})();
