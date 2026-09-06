(async function () {
  const usuario = await protegerPagina({ admin: true });
  if (!usuario) return;

  const contenedor = document.getElementById('lista-solicitudes');

  async function cargar() {
    const resultado = await peticionGet('/admin/solicitudes?por_pagina=100');
    const solicitudes = resultado.datos.datos || [];
    contenedor.textContent = '';

    if (solicitudes.length === 0) {
      contenedor.appendChild(crearElemento('p', 'No hay solicitudes de reclamación todavía.'));
      return;
    }

    solicitudes.forEach(solicitud => {
      const tarjeta = crearElemento('div', null, 'card');

      tarjeta.appendChild(crearElemento('h3', solicitud.objeto_nombre));
      tarjeta.appendChild(crearBadge(solicitud.estado, claseBadgeEstado(solicitud.estado)));
      tarjeta.appendChild(crearElemento('p', 'Solicitante: ' + solicitud.solicitante_nombre));
      tarjeta.appendChild(crearElemento('p', 'Contacto: ' + solicitud.contacto));
      tarjeta.appendChild(crearElemento('p', 'Mensaje de verificación: ' + solicitud.mensaje));
      if (solicitud.respuesta_admin) {
        tarjeta.appendChild(crearElemento('p', 'Respuesta del admin: ' + solicitud.respuesta_admin));
      }

      const verObjeto = crearElemento('a', 'Ver reporte', 'btn btn-secondary btn-small');
      verObjeto.href = `detalle-objeto.html?id=${solicitud.objeto_id}`;
      tarjeta.appendChild(verObjeto);

      if (solicitud.estado === 'pendiente' || solicitud.estado === 'en_revision') {
        const aprobar = crearElemento('button', 'Aprobar', 'btn btn-primary btn-small');
        aprobar.style.marginLeft = '0.5rem';
        aprobar.addEventListener('click', () => revisar(solicitud.id, 'aprobada'));

        const rechazar = crearElemento('button', 'Rechazar', 'btn btn-danger btn-small');
        rechazar.style.marginLeft = '0.5rem';
        rechazar.addEventListener('click', () => revisar(solicitud.id, 'rechazada'));

        tarjeta.appendChild(aprobar);
        tarjeta.appendChild(rechazar);
      }

      contenedor.appendChild(tarjeta);
    });
  }

  async function revisar(solicitudId, estado) {
    const respuestaAdmin = prompt('Comentario para el solicitante (opcional):') || '';
    const resultado = await peticionProtegida(`/admin/solicitudes/${solicitudId}`, 'PUT', {
      estado, respuesta_admin: respuestaAdmin,
    });
    if (!resultado.ok) {
      alert(resultado.datos.mensaje || 'No se pudo actualizar la solicitud');
    }
    cargar();
  }

  cargar();
})();
