(async function () {
  const usuario = await protegerPagina({ admin: true });
  if (!usuario) return;

  // No existe un endpoint único de "estadísticas": se arman a partir de los
  // totales que ya devuelve cada listado paginado (por_pagina=1 solo para
  // leer el campo "total", sin traer datos que no se van a usar).
  const [activos, enProceso, usuarios, solicitudesPendientes] = await Promise.all([
    peticionGet('/objetos?estado=activo&por_pagina=1'),
    peticionGet('/objetos?estado=en_proceso&por_pagina=1'),
    peticionGet('/admin/usuarios?por_pagina=1'),
    peticionGet('/admin/solicitudes?estado=pendiente&por_pagina=1'),
  ]);

  const [resueltos, cerrados, cancelados] = await Promise.all([
    peticionGet('/admin/objetos?estado=resuelto&por_pagina=1'),
    peticionGet('/admin/objetos?estado=cerrado&por_pagina=1'),
    peticionGet('/admin/objetos?estado=cancelado&por_pagina=1'),
  ]);

  const totalReportes = [activos, enProceso, resueltos, cerrados, cancelados]
    .reduce((suma, r) => suma + (r.datos.total || 0), 0);

  document.getElementById('total-reportes').textContent = totalReportes;
  document.getElementById('reportes-activos').textContent = activos.datos.total || 0;
  document.getElementById('total-usuarios').textContent = usuarios.datos.total || 0;
  document.getElementById('solicitudes-pendientes').textContent = solicitudesPendientes.datos.total || 0;
})();
