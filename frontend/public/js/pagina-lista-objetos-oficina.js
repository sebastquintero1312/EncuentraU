/* Lista de todos los reportes para la oficina. La usan el encargado
   (encargado-objetos.html, con acciones) y el administrador
   (admin-objetos.html, solo lectura). */

const filtrosOficina = { q: '', tipo: '', estado: '', categoria_id: '', pagina: 1 };

function rutaListaOficina(rol) {
  return rol === 'administrador' ? '/admin/objetos' : '/encargado/objetos';
}

function filaObjetoOficina(objeto, rol) {
  const ver = el('a', { clase: 'boton boton-secundario boton-pequeno', href: `oficina-objeto.html?id=${encodeURIComponent(objeto.id)}` }, ['Abrir', icono('arrow-right')]);
  const acciones = el('div', { clase: 'acciones-tabla' }, [ver]);
  if (rol === 'encargado' && objeto.estado === 'pendiente_entrega') {
    acciones.prepend(el('a', { clase: 'boton boton-primario boton-pequeno', href: `oficina-objeto.html?id=${encodeURIComponent(objeto.id)}#recepcion` }, [icono('box-archive'), 'Recibir']));
  }
  if (rol === 'encargado' && objeto.estado === 'reservado') {
    acciones.prepend(el('a', { clase: 'boton boton-exito boton-pequeno', href: `oficina-objeto.html?id=${encodeURIComponent(objeto.id)}#entrega` }, [icono('handshake'), 'Entregar']));
  }
  return el('tr', {}, [
    el('td', {}, [
      el('strong', { texto: objeto.nombre }),
      el('div', { clase: 'texto-suave texto-pequeno', texto: `${objeto.categoria} · ${objeto.ubicacion}` }),
    ]),
    el('td', {}, insigniaTipo(objeto.tipo)),
    el('td', { texto: objeto.reportado_por ? objeto.reportado_por.nombre : '' }),
    el('td', { texto: formatearFecha(objeto.fecha_evento) }),
    el('td', {}, insigniaEstado(objeto.estado, objeto.estado_nombre)),
    el('td', {}, acciones),
  ]);
}

async function cargarObjetosOficina(rol) {
  const cuerpo = document.getElementById('cuerpo-tabla');
  vaciar(cuerpo);
  cuerpo.append(el('tr', {}, el('td', { colspan: '6' }, estadoCargando())));
  const resultado = await peticionGet(rutaListaOficina(rol), { ...filtrosOficina, por_pagina: 15 });
  vaciar(cuerpo);
  if (!resultado.ok) {
    cuerpo.append(el('tr', {}, el('td', { colspan: '6' }, el('div', { clase: 'alerta alerta-error', texto: resultado.datos.mensaje }))));
    return;
  }
  if (!resultado.datos.datos.length) {
    cuerpo.append(el('tr', {}, el('td', { colspan: '6' }, estadoVacio('No hay reportes con estos filtros.', 'box-open'))));
  }
  resultado.datos.datos.forEach((objeto) => cuerpo.append(filaObjetoOficina(objeto, rol)));
  pintarPaginacion(document.getElementById('paginacion'), resultado.datos, (pagina) => {
    filtrosOficina.pagina = pagina;
    cargarObjetosOficina(rol);
  });
}

sesionLista.then(async (usuario) => {
  const rol = usuario.rol;
  ['tipo', 'estado', 'categoria_id', 'q'].forEach((clave) => {
    if (parametroUrl(clave)) filtrosOficina[clave] = parametroUrl(clave);
  });

  const catalogos = await peticionGet('/catalogos');
  const selectEstado = document.getElementById('estado');
  const selectCategoria = document.getElementById('categoria');
  if (catalogos.ok) {
    const estados = [];
    const vistos = new Set();
    ['encontrado', 'perdido'].forEach((tipo) => catalogos.datos.estados[tipo].forEach((estado) => {
      if (vistos.has(estado.codigo)) return;
      vistos.add(estado.codigo);
      estados.push({ valor: estado.codigo, texto: estado.nombre });
    }));
    llenarSelect(selectEstado, estados, 'Todos los estados');
    llenarSelect(selectCategoria, catalogos.datos.categorias.map((c) => ({ valor: c.id, texto: c.nombre })), 'Todas las categorías');
  }
  selectEstado.value = filtrosOficina.estado;
  selectCategoria.value = filtrosOficina.categoria_id;
  document.getElementById('texto').value = filtrosOficina.q;

  document.querySelectorAll('#pildoras-tipo .pildora').forEach((pildora) => {
    pildora.classList.toggle('activa', pildora.dataset.tipo === filtrosOficina.tipo);
    pildora.addEventListener('click', () => {
      document.querySelectorAll('#pildoras-tipo .pildora').forEach((p) => p.classList.remove('activa'));
      pildora.classList.add('activa');
      filtrosOficina.tipo = pildora.dataset.tipo;
      filtrosOficina.pagina = 1;
      cargarObjetosOficina(rol);
    });
  });
  selectEstado.addEventListener('change', () => { filtrosOficina.estado = selectEstado.value; filtrosOficina.pagina = 1; cargarObjetosOficina(rol); });
  selectCategoria.addEventListener('change', () => { filtrosOficina.categoria_id = selectCategoria.value; filtrosOficina.pagina = 1; cargarObjetosOficina(rol); });
  let espera = null;
  document.getElementById('texto').addEventListener('input', (evento) => {
    clearTimeout(espera);
    espera = setTimeout(() => { filtrosOficina.q = evento.target.value.trim(); filtrosOficina.pagina = 1; cargarObjetosOficina(rol); }, 350);
  });

  cargarObjetosOficina(rol);
});
