/* Búsqueda de objetos que están en la oficina (solo datos públicos).
   Los filtros se reflejan en la URL (?q=...&categoria_id=...) para que se
   puedan compartir o recargar, igual que el buscador de programas del
   sitio de la universidad. */

const filtrosBusqueda = { q: '', categoria_id: '', ubicacion_id: '', desde: '', hasta: '', pagina: 1 };

function leerFiltrosDeLaUrl() {
  const parametros = new URLSearchParams(window.location.search);
  Object.keys(filtrosBusqueda).forEach((clave) => {
    if (parametros.get(clave)) filtrosBusqueda[clave] = parametros.get(clave);
  });
  filtrosBusqueda.pagina = Number(filtrosBusqueda.pagina) || 1;
}

function escribirFiltrosEnLaUrl() {
  const parametros = new URLSearchParams();
  Object.entries(filtrosBusqueda).forEach(([clave, valor]) => {
    if (valor && !(clave === 'pagina' && Number(valor) === 1)) parametros.set(clave, valor);
  });
  const consulta = parametros.toString();
  window.history.replaceState(null, '', window.location.pathname + (consulta ? `?${consulta}` : ''));
}

async function buscar() {
  escribirFiltrosEnLaUrl();
  const resultados = document.getElementById('resultados');
  const resumen = document.getElementById('resumen-resultados');
  vaciar(resultados);
  resultados.append(estadoCargando());

  const respuesta = await peticionGet('/objetos', { ...filtrosBusqueda, por_pagina: 12 });
  vaciar(resultados);
  if (!respuesta.ok) {
    resultados.append(el('div', { clase: 'alerta alerta-error', texto: respuesta.datos.mensaje }));
    return;
  }
  const { datos, total } = respuesta.datos;
  resumen.textContent = total === 1 ? '1 objeto en la oficina' : `${total} objetos en la oficina`;
  if (!datos.length) {
    resultados.append(estadoVacio('No hay objetos que coincidan con tu búsqueda.', 'magnifying-glass'));
  }
  datos.forEach((objeto) => resultados.append(tarjetaObjeto(objeto, `detalle-objeto.html?id=${encodeURIComponent(objeto.id)}`)));
  pintarPaginacion(document.getElementById('paginacion'), respuesta.datos, (pagina) => {
    filtrosBusqueda.pagina = pagina;
    buscar();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });
}

function pintarPildoras(categorias) {
  const contenedor = document.getElementById('pildoras-categoria');
  vaciar(contenedor);
  const opciones = [{ id: '', nombre: 'Todas' }, ...categorias];
  opciones.forEach((categoria) => {
    const activa = String(filtrosBusqueda.categoria_id) === String(categoria.id);
    const pildora = el('button', {
      type: 'button',
      clase: 'pildora' + (activa ? ' activa' : ''),
      'aria-pressed': String(activa),
      texto: categoria.nombre,
    });
    pildora.addEventListener('click', () => {
      filtrosBusqueda.categoria_id = categoria.id;
      filtrosBusqueda.pagina = 1;
      pintarPildoras(categorias);
      buscar();
    });
    contenedor.append(pildora);
  });
}

sesionLista.then(async () => {
  leerFiltrosDeLaUrl();
  const texto = document.getElementById('texto');
  const ubicacion = document.getElementById('ubicacion');
  const desde = document.getElementById('desde');
  const hasta = document.getElementById('hasta');
  texto.value = filtrosBusqueda.q;
  desde.value = filtrosBusqueda.desde;
  hasta.value = filtrosBusqueda.hasta;
  desde.max = hoyISO();
  hasta.max = hoyISO();

  const catalogos = await peticionGet('/catalogos');
  if (catalogos.ok) {
    pintarPildoras(catalogos.datos.categorias);
    llenarSelect(ubicacion, catalogos.datos.ubicaciones.map((u) => ({ valor: u.id, texto: u.nombre })), 'Todas las ubicaciones');
    ubicacion.value = filtrosBusqueda.ubicacion_id;
  }

  let espera = null;
  texto.addEventListener('input', () => {
    clearTimeout(espera);
    espera = setTimeout(() => { filtrosBusqueda.q = texto.value.trim(); filtrosBusqueda.pagina = 1; buscar(); }, 350);
  });
  document.getElementById('form-busqueda').addEventListener('submit', (evento) => {
    evento.preventDefault();
    filtrosBusqueda.q = texto.value.trim();
    filtrosBusqueda.pagina = 1;
    buscar();
  });
  [[ubicacion, 'ubicacion_id'], [desde, 'desde'], [hasta, 'hasta']].forEach(([control, clave]) => {
    control.addEventListener('change', () => { filtrosBusqueda[clave] = control.value; filtrosBusqueda.pagina = 1; buscar(); });
  });
  document.getElementById('boton-limpiar').addEventListener('click', () => {
    Object.assign(filtrosBusqueda, { q: '', categoria_id: '', ubicacion_id: '', desde: '', hasta: '', pagina: 1 });
    texto.value = ''; ubicacion.value = ''; desde.value = ''; hasta.value = '';
    if (catalogos.ok) pintarPildoras(catalogos.datos.categorias);
    buscar();
  });

  buscar();
});
