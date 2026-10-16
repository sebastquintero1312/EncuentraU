/* Notificaciones del usuario (cualquier rol). */

let soloNoLeidas = '';

async function marcarLeida(notificacion, item) {
  const resultado = await peticionProtegida(`/notificaciones/${encodeURIComponent(notificacion.id)}/leida`, 'POST');
  if (resultado.ok) {
    item.classList.remove('no-leida');
    actualizarContadorNotificaciones();
  }
}

async function cargarNotificaciones() {
  const lista = document.getElementById('lista-notificaciones');
  vaciar(lista);
  lista.append(estadoCargando());
  const resultado = await peticionGet('/notificaciones', { no_leidas: soloNoLeidas });
  vaciar(lista);
  if (!resultado.ok) {
    lista.append(el('div', { clase: 'alerta alerta-error', texto: resultado.datos.mensaje }));
    return;
  }
  const datos = resultado.datos.datos;
  if (!datos.length) {
    lista.append(estadoVacio('No tienes avisos.', 'bell-slash'));
    return;
  }
  lista.append(el('ul', { clase: 'lista-items' }, datos.map((notificacion) => {
    const acciones = el('div', { clase: 'grupo-botones' });
    const item = el('li', { clase: 'item' + (notificacion.leida ? '' : ' no-leida') });
    // El enlace lo genera el servidor, pero igual se valida que sea una
    // página interna antes de usarlo (defensa en profundidad).
    if (notificacion.enlace && esPaginaInterna(notificacion.enlace)) {
      const ver = el('a', { clase: 'boton boton-secundario boton-pequeno', href: notificacion.enlace }, ['Ver', icono('arrow-right')]);
      ver.addEventListener('click', () => { if (!notificacion.leida) marcarLeida(notificacion, item); });
      acciones.append(ver);
    }
    if (!notificacion.leida) {
      const leer = el('button', { clase: 'boton boton-secundario boton-pequeno', type: 'button', title: 'Marcar como leída' }, icono('check'));
      leer.addEventListener('click', () => { marcarLeida(notificacion, item); leer.remove(); });
      acciones.append(leer);
    }
    item.append(
      el('div', { clase: 'principal' }, [
        el('h4', { texto: notificacion.titulo }),
        el('p', { clase: 'mb-0 texto-suave', texto: notificacion.mensaje }),
        el('div', { clase: 'meta mt-1' }, [el('span', {}, [icono('clock'), ' ', formatearFechaHora(notificacion.created_at)])]),
      ]),
      acciones,
    );
    return item;
  })));
}

sesionLista.then(() => {
  document.querySelectorAll('.pildora[data-filtro]').forEach((pildora) => {
    pildora.addEventListener('click', () => {
      document.querySelectorAll('.pildora[data-filtro]').forEach((p) => p.classList.remove('activa'));
      pildora.classList.add('activa');
      soloNoLeidas = pildora.dataset.filtro;
      cargarNotificaciones();
    });
  });
  document.getElementById('boton-leer-todas').addEventListener('click', async () => {
    const resultado = await peticionProtegida('/notificaciones/leer-todas', 'POST');
    if (resultado.ok) {
      actualizarContadorNotificaciones();
      cargarNotificaciones();
    }
  });
  cargarNotificaciones();
});
