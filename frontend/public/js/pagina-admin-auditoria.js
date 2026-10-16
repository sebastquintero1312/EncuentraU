/* Consulta de la auditoría. Los datos "antes" y "después" se muestran como
   texto (JSON) con textContent: aunque contengan HTML escrito por un
   usuario, nunca se interpretan. */

const NOMBRE_OPERACION = { INSERT: 'Creó', UPDATE: 'Modificó', DELETE: 'Borró' };
const NOMBRE_TABLA = {
  usuarios: 'usuario', objetos: 'reporte', solicitudes: 'reclamación', entregas: 'entrega',
  tokens_usuario: 'token', categorias: 'categoría', ubicaciones: 'ubicación', parametros: 'parámetro',
};
const CAMPOS_FILTRO = ['tabla', 'operacion', 'registro_id', 'desde', 'hasta', 'usuario_id', 'transaccion_id'];
let paginaAuditoria = 1;

function leerFiltrosAuditoria() {
  const formulario = document.getElementById('form-filtros');
  const filtros = {};
  CAMPOS_FILTRO.forEach((campo) => { filtros[campo] = formulario.elements[campo].value; });
  return filtros;
}

function detalleCambio(fila) {
  const contenido = [];
  if (fila.campos_modificados.length) {
    contenido.push(el('div', {}, fila.campos_modificados.map((campo) => el('span', { clase: 'campo-cambiado', texto: campo }))));
  }
  const antes = fila.datos_anteriores || {};
  const despues = fila.datos_nuevos || {};
  let resumen = {};
  if (fila.operacion === 'UPDATE') {
    fila.campos_modificados.forEach((campo) => {
      resumen[campo] = campo in despues ? { antes: antes[campo], despues: despues[campo] } : '(dato secreto: no se guarda en la auditoría)';
    });
  } else {
    resumen = fila.operacion === 'INSERT' ? despues : antes;
  }
  contenido.push(el('details', {}, [
    el('summary', { texto: fila.operacion === 'UPDATE' ? 'Ver antes y después' : 'Ver datos' }),
    el('pre', { clase: 'json', texto: JSON.stringify(resumen, null, 2) }),
  ]));
  return contenido;
}

function filtrarPorTransaccion(transaccionId) {
  const formulario = document.getElementById('form-filtros');
  formulario.reset();
  formulario.elements.usuario_id.value = '';
  formulario.elements.transaccion_id.value = transaccionId;
  paginaAuditoria = 1;
  cargarAuditoria();
}

async function cargarAuditoria() {
  const cuerpo = document.getElementById('cuerpo-tabla');
  const filtros = leerFiltrosAuditoria();
  vaciar(cuerpo);
  cuerpo.append(el('tr', {}, el('td', { colspan: '5' }, estadoCargando())));

  const aviso = document.getElementById('filtro-activo');
  vaciar(aviso);
  if (filtros.transaccion_id) aviso.append(el('span', { clase: 'insignia insignia-naranja', texto: `Mostrando solo la transacción ${filtros.transaccion_id}` }));
  if (filtros.usuario_id) aviso.append(el('span', { clase: 'insignia insignia-naranja', texto: `Mostrando solo acciones del usuario #${filtros.usuario_id}` }));

  const resultado = await peticionGet('/admin/auditoria', { ...filtros, pagina: paginaAuditoria, por_pagina: 25 });
  vaciar(cuerpo);
  if (!resultado.ok) {
    cuerpo.append(el('tr', {}, el('td', { colspan: '5' }, el('div', { clase: 'alerta alerta-error', texto: resultado.datos.mensaje }))));
    return;
  }
  if (!resultado.datos.datos.length) {
    cuerpo.append(el('tr', {}, el('td', { colspan: '5' }, estadoVacio('No hay registros con estos filtros.', 'clipboard'))));
  }
  resultado.datos.datos.forEach((fila) => {
    const transaccion = el('button', { clase: 'boton boton-secundario boton-pequeno', type: 'button', title: 'Ver todos los cambios hechos en la misma transacción' }, [icono('link'), `Tx ${fila.transaccion_id}`]);
    transaccion.addEventListener('click', () => filtrarPorTransaccion(fila.transaccion_id));
    cuerpo.append(el('tr', {}, [
      el('td', { texto: formatearFechaHora(fila.fecha) }),
      el('td', {}, [
        el('strong', { texto: fila.usuario_nombre }),
        fila.usuario_rol ? el('div', { clase: 'texto-suave texto-pequeno', texto: NOMBRE_ROL[fila.usuario_rol] || fila.usuario_rol }) : null,
        fila.ip ? el('div', { clase: 'texto-suave texto-pequeno', texto: `IP ${fila.ip}` }) : null,
      ]),
      el('td', {}, [
        el('span', { clase: `insignia ${fila.operacion === 'INSERT' ? 'insignia-verde' : fila.operacion === 'UPDATE' ? 'insignia-azul' : 'insignia-rojo'}`, texto: NOMBRE_OPERACION[fila.operacion] }),
        el('div', { clase: 'texto-pequeno mt-1', texto: NOMBRE_TABLA[fila.tabla] || fila.tabla }),
      ]),
      el('td', {}, [el('div', { texto: fila.registro_id ? `#${fila.registro_id}` : '—' }), transaccion]),
      el('td', {}, detalleCambio(fila)),
    ]));
  });
  pintarPaginacion(document.getElementById('paginacion'), resultado.datos, (pagina) => { paginaAuditoria = pagina; cargarAuditoria(); });
}

sesionLista.then(() => {
  const formulario = document.getElementById('form-filtros');
  CAMPOS_FILTRO.forEach((campo) => {
    const valor = parametroUrl(campo);
    if (valor) formulario.elements[campo].value = valor;
  });
  formulario.addEventListener('submit', (evento) => { evento.preventDefault(); paginaAuditoria = 1; cargarAuditoria(); });
  document.getElementById('boton-limpiar').addEventListener('click', () => {
    formulario.reset();
    formulario.elements.usuario_id.value = '';
    formulario.elements.transaccion_id.value = '';
    paginaAuditoria = 1;
    cargarAuditoria();
  });
  cargarAuditoria();
});
