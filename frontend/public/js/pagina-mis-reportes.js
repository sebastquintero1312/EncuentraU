(async function () {
  const usuario = await protegerPagina();
  if (!usuario) return;

  const cuerpoTabla = document.getElementById('cuerpo-tabla');

  async function cargar() {
    const resultado = await peticionGet('/mis-reportes?por_pagina=50');
    cuerpoTabla.textContent = '';

    const reportes = resultado.datos.datos || [];
    if (reportes.length === 0) {
      const fila = document.createElement('tr');
      const celda = crearElemento('td', 'Todavía no has creado ningún reporte.');
      celda.colSpan = 6;
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

      fila.appendChild(crearElemento('td', reporte.ubicacion));
      fila.appendChild(crearElemento('td', reporte.fecha_evento));

      const celdaEstado = crearElemento('td');
      celdaEstado.appendChild(crearBadge(reporte.estado, claseBadgeEstado(reporte.estado)));
      fila.appendChild(celdaEstado);

      const celdaAcciones = crearElemento('td');
      const verDetalle = crearElemento('a', 'Ver detalle', 'btn btn-secondary btn-small');
      verDetalle.href = `detalle-objeto.html?id=${reporte.id}`;
      celdaAcciones.appendChild(verDetalle);

      if (reporte.estado === 'activo' || reporte.estado === 'en_proceso') {
        const cancelar = crearElemento('button', 'Cancelar', 'btn btn-danger btn-small');
        cancelar.style.marginLeft = '0.5rem';
        cancelar.addEventListener('click', async () => {
          if (!confirm('¿Cancelar este reporte?')) return;
          await peticionProtegida(`/objetos/${reporte.id}`, 'DELETE');
          cargar();
        });
        celdaAcciones.appendChild(cancelar);
      }
      fila.appendChild(celdaAcciones);

      cuerpoTabla.appendChild(fila);
    });
  }

  cargar();
})();
