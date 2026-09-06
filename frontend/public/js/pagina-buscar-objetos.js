function pintarResultados(reportes) {
  const contenedor = document.getElementById('resultados');
  contenedor.textContent = '';

  if (reportes.length === 0) {
    contenedor.appendChild(crearElemento('p', 'No se encontraron objetos con esos filtros.'));
    return;
  }

  reportes.forEach(reporte => {
    const tarjeta = crearElemento('div', null, 'card');

    tarjeta.appendChild(crearElemento('h3', reporte.nombre));

    const linea1 = crearElemento('p');
    linea1.appendChild(crearBadge(reporte.tipo, 'badge-' + reporte.tipo));
    linea1.appendChild(document.createTextNode(' · ' + reporte.categoria));
    tarjeta.appendChild(linea1);

    tarjeta.appendChild(crearElemento('p', `${reporte.ubicacion} — ${reporte.fecha_evento}`));

    const verDetalle = crearElemento('a', 'Ver detalle', 'btn btn-secondary btn-small');
    verDetalle.href = `detalle-objeto.html?id=${reporte.id}`;
    tarjeta.appendChild(verDetalle);

    contenedor.appendChild(tarjeta);
  });
}

async function buscar() {
  const texto = document.getElementById('texto').value.trim();
  const tipo = document.getElementById('tipo').value;
  const categoria = document.getElementById('categoria').value;

  const parametros = new URLSearchParams({ por_pagina: '50' });
  if (texto) parametros.set('q', texto);
  if (tipo) parametros.set('tipo', tipo);
  if (categoria) parametros.set('categoria', categoria);

  const resultado = await peticionGet('/objetos?' + parametros.toString());
  pintarResultados(resultado.datos.datos || []);
}

document.getElementById('btn-buscar').addEventListener('click', buscar);

// Al cargar la página se muestran todos los reportes activos
buscar();
