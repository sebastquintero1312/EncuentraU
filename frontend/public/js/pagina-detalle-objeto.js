(async function () {
  const contenedor = document.getElementById('detalle');
  const parametros = new URLSearchParams(window.location.search);
  const id = parametros.get('id');

  const usuarioActual = await obtenerSesion();

  const resultado = await peticionGet(`/objetos/${id}`);
  if (!resultado.ok) {
    contenedor.textContent = '';
    contenedor.appendChild(crearElemento('p', 'No se encontró ningún reporte con ese id.'));
    const volver = crearElemento('a', 'Volver a buscar', 'btn btn-secondary');
    volver.href = 'buscar-objetos.html';
    contenedor.appendChild(volver);
    return;
  }

  const reporte = resultado.datos.objeto;
  const coincidencias = resultado.datos.coincidencias || [];
  const esDueno = usuarioActual && usuarioActual.id === reporte.usuario_id;

  contenedor.textContent = '';
  contenedor.appendChild(crearElemento('h2', reporte.nombre));

  const lineaEstado = crearElemento('div', null, 'estado-linea');
  lineaEstado.appendChild(crearBadge(reporte.tipo, 'badge-' + reporte.tipo));
  lineaEstado.appendChild(crearBadge(reporte.estado, claseBadgeEstado(reporte.estado)));
  contenedor.appendChild(lineaEstado);

  const lista = document.createElement('dl');
  const agregar = (etiqueta, valor) => {
    lista.appendChild(crearElemento('dt', etiqueta));
    lista.appendChild(crearElemento('dd', valor));
  };
  agregar('Categoría', reporte.categoria);
  agregar('Descripción', reporte.descripcion);
  agregar('Ubicación', reporte.ubicacion);
  agregar('Fecha', reporte.fecha_evento);
  agregar('Reportado por', reporte.usuario_nombre);
  contenedor.appendChild(lista);

  contenedor.appendChild(document.createElement('br'));

  if (usuarioActual && !esDueno && (reporte.estado === 'activo' || reporte.estado === 'en_proceso')) {
    const solicitar = crearElemento('a', 'Solicitar recuperación', 'btn btn-primary');
    solicitar.href = `solicitud-recuperacion.html?id=${reporte.id}`;
    contenedor.appendChild(solicitar);
  }
  const volverBuscar = crearElemento('a', 'Volver a buscar', 'btn btn-secondary');
  volverBuscar.href = 'buscar-objetos.html';
  contenedor.appendChild(volverBuscar);

  // Posibles coincidencias: solo una pista, nunca propiedad confirmada.
  if (coincidencias.length > 0) {
    contenedor.appendChild(crearElemento('h3', 'Posibles coincidencias'));
    contenedor.appendChild(crearElemento('p', 'Estos reportes podrían corresponder al mismo objeto. Esto NO confirma que sean tuyos: usa "Solicitar recuperación" para iniciar la verificación.'));
    const grid = crearElemento('div', null, 'grid');
    coincidencias.forEach(c => {
      const tarjeta = crearElemento('div', null, 'card');
      tarjeta.appendChild(crearElemento('h3', c.nombre));
      const linea = crearElemento('p');
      linea.appendChild(crearBadge(c.tipo, 'badge-' + c.tipo));
      linea.appendChild(document.createTextNode(' · ' + c.categoria));
      tarjeta.appendChild(linea);
      tarjeta.appendChild(crearElemento('p', `${c.ubicacion} — ${c.fecha_evento}`));
      const verDetalle = crearElemento('a', 'Ver detalle', 'btn btn-secondary btn-small');
      verDetalle.href = `detalle-objeto.html?id=${c.id}`;
      tarjeta.appendChild(verDetalle);
      grid.appendChild(tarjeta);
    });
    contenedor.appendChild(grid);
  }

  // Si soy el dueño del reporte, veo las solicitudes de reclamación recibidas
  // (incluye información privada de verificación: solo yo o un admin la vemos).
  if (esDueno) {
    const solicitudesResp = await peticionGet(`/objetos/${reporte.id}/solicitudes`);
    const solicitudes = solicitudesResp.datos.datos || [];
    contenedor.appendChild(crearElemento('h3', 'Solicitudes de reclamación recibidas'));
    if (solicitudes.length === 0) {
      contenedor.appendChild(crearElemento('p', 'Todavía no has recibido ninguna solicitud.'));
    } else {
      solicitudes.forEach(s => {
        const tarjeta = crearElemento('div', null, 'card');
        tarjeta.appendChild(crearBadge(s.estado, claseBadgeEstado(s.estado)));
        tarjeta.appendChild(crearElemento('p', 'De: ' + s.solicitante_nombre));
        tarjeta.appendChild(crearElemento('p', 'Contacto: ' + s.contacto));
        tarjeta.appendChild(crearElemento('p', s.mensaje));
        contenedor.appendChild(tarjeta);
      });
    }
  }
})();
