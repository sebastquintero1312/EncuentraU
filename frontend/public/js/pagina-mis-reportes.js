/* Lista de los reportes del estudiante (perdidos y encontrados). */

const AYUDA_ESTADO = {
  pendiente_entrega: 'Llévalo a la oficina para que aparezca en la búsqueda.',
  en_oficina: 'La oficina lo tiene en custodia.',
  reservado: 'Hay una reclamación pre-aprobada: su dueño debe retirarlo.',
  entregado: 'Volvió a su dueño. ¡Gracias!',
  buscando: 'Te avisaremos si llega algo parecido a la oficina.',
  recuperado: '¡Recuperaste tu objeto!',
};

let tipoMisReportes = '';

async function cargarMisReportes(pagina) {
  const lista = document.getElementById('lista-reportes');
  vaciar(lista);
  lista.append(estadoCargando());
  const resultado = await peticionGet('/mis-reportes', { tipo: tipoMisReportes, pagina, por_pagina: 10 });
  vaciar(lista);
  if (!resultado.ok) {
    lista.append(el('div', { clase: 'alerta alerta-error', texto: resultado.datos.mensaje }));
    return;
  }
  const { datos } = resultado.datos;
  if (!datos.length) {
    lista.append(estadoVacio('No tienes reportes de este tipo.', 'clipboard'));
  } else {
    lista.append(el('ul', { clase: 'lista-items' }, datos.map((objeto) => el('li', { clase: 'item' }, [
      el('div', { clase: 'icono-circulo mb-0' }, icono(iconoCategoria(objeto.categoria))),
      el('div', { clase: 'principal' }, [
        el('h4', {}, el('a', { href: `detalle-objeto.html?id=${encodeURIComponent(objeto.id)}`, texto: objeto.nombre })),
        el('div', { clase: 'meta' }, [
          insigniaTipo(objeto.tipo),
          el('span', {}, [icono('location-dot'), ' ', objeto.ubicacion]),
          el('span', {}, [icono('calendar'), ' ', formatearFecha(objeto.fecha_evento)]),
        ]),
        AYUDA_ESTADO[objeto.estado] ? el('p', { clase: 'texto-suave texto-pequeno mt-1 mb-0', texto: AYUDA_ESTADO[objeto.estado] }) : null,
      ]),
      insigniaEstado(objeto.estado, objeto.estado_nombre),
    ]))));
  }
  pintarPaginacion(document.getElementById('paginacion'), resultado.datos, cargarMisReportes);
}

sesionLista.then(() => {
  document.querySelectorAll('#pildoras-tipo .pildora').forEach((pildora) => {
    pildora.addEventListener('click', () => {
      document.querySelectorAll('#pildoras-tipo .pildora').forEach((p) => p.classList.remove('activa'));
      pildora.classList.add('activa');
      tipoMisReportes = pildora.dataset.tipo;
      cargarMisReportes(1);
    });
  });
  cargarMisReportes(1);
});
