/* ============================================
   MAIN.JS
   ============================================
   Funciones generales que se usan en varias páginas.

   REGLA DE SEGURIDAD (XSS): NUNCA se usa innerHTML con datos que vienen
   de la API (nombres de objetos, descripciones, nombres de personas...).
   Esos textos los escribe un usuario y podrían contener HTML/JS. Todo se
   construye con document.createElement y textContent (ver la función el()).
*/

// Crea un elemento del DOM de forma segura.
//   el('a', { clase: 'boton', href: 'x.html' }, ['Texto', otroNodo])
// Los textos se agregan como nodos de texto: el navegador nunca los
// interpreta como HTML.
function el(etiqueta, atributos, hijos) {
  const nodo = document.createElement(etiqueta);
  Object.entries(atributos || {}).forEach(([clave, valor]) => {
    if (valor === null || valor === undefined || valor === false) return;
    if (clave === 'clase') nodo.className = valor;
    else if (clave === 'texto') nodo.textContent = valor;
    else if (clave.startsWith('on') && typeof valor === 'function') nodo.addEventListener(clave.slice(2), valor);
    else nodo.setAttribute(clave, valor === true ? '' : String(valor));
  });
  [].concat(hijos === undefined ? [] : hijos).forEach((hijo) => {
    if (hijo === null || hijo === undefined || hijo === false) return;
    nodo.append(hijo instanceof Node ? hijo : document.createTextNode(String(hijo)));
  });
  return nodo;
}

// Atajo compatible con páginas anteriores
function crearElemento(etiqueta, texto, claseCss) {
  return el(etiqueta, { clase: claseCss, texto });
}

function icono(nombre, claseExtra) {
  return el('i', { clase: `fa-solid fa-${nombre}${claseExtra ? ' ' + claseExtra : ''}`, 'aria-hidden': 'true' });
}

function vaciar(nodo) {
  while (nodo.firstChild) nodo.removeChild(nodo.firstChild);
}

function parametroUrl(nombre) {
  return new URLSearchParams(window.location.search).get(nombre);
}

// Solo se aceptan páginas internas (evita "open redirect": que un enlace
// manipulado mande al usuario a un sitio externo después de iniciar sesión).
function esPaginaInterna(ruta) {
  return typeof ruta === 'string' && /^[a-z0-9-]+\.html(\?[a-zA-Z0-9=&_-]*)?$/.test(ruta);
}

/* ---------- Fechas ---------- */

// "2026-10-15" (sin hora) se interpreta como fecha LOCAL, no UTC
// (con new Date('2026-10-15') se correría un día en Colombia).
function _fechaDesdeTexto(texto) {
  if (!texto) return null;
  if (/^\d{4}-\d{2}-\d{2}$/.test(texto)) {
    const [a, m, d] = texto.split('-').map(Number);
    return new Date(a, m - 1, d);
  }
  const fecha = new Date(texto);
  return isNaN(fecha) ? null : fecha;
}

function formatearFecha(texto) {
  const fecha = _fechaDesdeTexto(texto);
  return fecha ? fecha.toLocaleDateString('es-CO', { day: 'numeric', month: 'short', year: 'numeric' }) : '—';
}

function formatearFechaHora(texto) {
  const fecha = _fechaDesdeTexto(texto);
  return fecha
    ? fecha.toLocaleString('es-CO', { day: 'numeric', month: 'short', year: 'numeric', hour: 'numeric', minute: '2-digit' })
    : '—';
}

function hoyISO() {
  const hoy = new Date();
  const mes = String(hoy.getMonth() + 1).padStart(2, '0');
  const dia = String(hoy.getDate()).padStart(2, '0');
  return `${hoy.getFullYear()}-${mes}-${dia}`;
}

/* ---------- Estados e insignias ---------- */

const COLOR_ESTADO = {
  // reportes
  buscando: 'azul', recuperado: 'verde', cerrado: 'gris', cancelado: 'gris',
  pendiente_entrega: 'ambar', en_oficina: 'verde', reservado: 'naranja', entregado: 'oscura',
  // reclamaciones
  pendiente: 'ambar', preaprobada: 'naranja', entregada: 'verde', rechazada: 'rojo',
  cancelada: 'gris', vencida: 'gris', descartada: 'gris',
};

const NOMBRE_ESTADO = {
  buscando: 'Buscando', recuperado: 'Recuperado', cerrado: 'Cerrado', cancelado: 'Cancelado',
  pendiente_entrega: 'Pendiente de entrega', en_oficina: 'En la oficina', reservado: 'Reservado',
  entregado: 'Entregado', pendiente: 'Pendiente', preaprobada: 'Pre-aprobada', entregada: 'Entregada',
  rechazada: 'Rechazada', cancelada: 'Cancelada', vencida: 'Vencida', descartada: 'Descartada',
};

function insigniaEstado(codigo, nombre) {
  return el('span', { clase: `insignia insignia-${COLOR_ESTADO[codigo] || 'gris'}`, texto: nombre || NOMBRE_ESTADO[codigo] || codigo });
}

function insigniaTipo(tipo) {
  return tipo === 'perdido'
    ? el('span', { clase: 'insignia insignia-azul' }, [icono('magnifying-glass'), 'Perdido'])
    : el('span', { clase: 'insignia insignia-violeta' }, [icono('hand-holding-heart'), 'Encontrado']);
}

const NOMBRE_ROL = { estudiante: 'Estudiante', encargado: 'Encargado', administrador: 'Administrador' };

// Evidencia del reporte de pérdida previo (dias = días entre el reporte de
// pérdida y el reporte del hallazgo; negativo = lo reportó después).
function textoReportePrevio(dias) {
  if (dias === null || dias === undefined) return null;
  if (dias < 0) return 'Reportó la pérdida DESPUÉS de que se encontrara el objeto';
  if (dias === 0) return 'Reportó la pérdida el mismo día, ANTES de que se reportara el hallazgo';
  return `Reportó la pérdida ${dias} ${dias === 1 ? 'día' : 'días'} ANTES de que se encontrara el objeto`;
}

/* ---------- Categorías: ícono y color de portada ---------- */

const ICONO_CATEGORIA = {
  'tecnología': 'laptop', 'documentos': 'id-card', 'llaves': 'key', 'billeteras y bolsos': 'wallet',
  'ropa': 'shirt', 'accesorios': 'glasses', 'útiles escolares': 'pencil', 'botellas y termos': 'bottle-water',
};

function iconoCategoria(nombre) {
  return ICONO_CATEGORIA[(nombre || '').toLowerCase()] || 'box-open';
}

function tonoCategoria(id) {
  return 'tono-' + ((Number(id) || 0) % 4 + 1);
}

/* ---------- Mensajes y formularios ---------- */

const ICONO_ALERTA = { error: 'circle-exclamation', exito: 'circle-check', info: 'circle-info', advertencia: 'triangle-exclamation', naranja: 'circle-info' };

function mostrarMensaje(contenedor, tipo, texto) {
  if (!contenedor) return;
  vaciar(contenedor);
  contenedor.className = `alerta alerta-${tipo}`;
  if (texto) {
    contenedor.append(icono(ICONO_ALERTA[tipo] || 'circle-info'), el('span', { texto }));
    contenedor.setAttribute('role', tipo === 'error' ? 'alert' : 'status');
  }
}

function limpiarMensaje(contenedor) {
  if (contenedor) vaciar(contenedor);
}

// Muestra los errores por campo que devuelve la API ({errores: {campo: mensaje}})
// debajo del input con name="campo".
function mostrarErroresCampos(formulario, errores) {
  limpiarErroresCampos(formulario);
  Object.entries(errores || {}).forEach(([campo, mensaje]) => {
    const input = formulario.querySelector(`[name="${campo}"]`);
    if (!input) return;
    const texto = Array.isArray(mensaje) ? mensaje.join('. ') : String(mensaje);
    mostrarError(input, texto);
  });
}

function limpiarErroresCampos(formulario) {
  formulario.querySelectorAll('.input-error').forEach((i) => i.classList.remove('input-error'));
  formulario.querySelectorAll('.mensaje-error').forEach((m) => { m.textContent = ''; });
}

// Mensaje general de una respuesta fallida (con los errores por campo si los hay)
function mensajeDeError(resultado) {
  const datos = resultado.datos || {};
  if (datos.errores) {
    const primeros = Object.values(datos.errores).map((m) => (Array.isArray(m) ? m[0] : m));
    return `${datos.mensaje || 'Revisa los datos'}: ${primeros.join(' · ')}`;
  }
  return datos.mensaje || 'Ocurrió un error inesperado';
}

function llenarSelect(select, opciones, textoVacio) {
  vaciar(select);
  if (textoVacio !== undefined) select.append(el('option', { value: '', texto: textoVacio }));
  opciones.forEach((opcion) => select.append(el('option', { value: opcion.valor, texto: opcion.texto })));
}

// Contador de caracteres para un textarea con maxlength
function conectarContador(campo) {
  const contador = document.querySelector(`[data-contador="${campo.id}"]`);
  if (!contador) return;
  const actualizar = () => { contador.textContent = `${campo.value.length}/${campo.maxLength}`; };
  campo.addEventListener('input', actualizar);
  actualizar();
}

function bloquearBoton(boton, textoCargando) {
  boton.disabled = true;
  boton.dataset.textoOriginal = boton.textContent;
  if (textoCargando) boton.textContent = textoCargando;
}

function desbloquearBoton(boton) {
  boton.disabled = false;
  if (boton.dataset.textoOriginal) boton.textContent = boton.dataset.textoOriginal;
}

/* ---------- Listas ---------- */

function estadoVacio(texto, nombreIcono) {
  return el('div', { clase: 'vacio' }, [icono(nombreIcono || 'inbox'), el('p', { texto })]);
}

function estadoCargando() {
  return el('div', { clase: 'cargando' }, [icono('spinner', 'fa-spin'), ' Cargando…']);
}

// Controles de "anterior / siguiente" para respuestas paginadas de la API
function pintarPaginacion(contenedor, datos, alCambiar) {
  vaciar(contenedor);
  const totalPaginas = Math.max(1, Math.ceil(datos.total / datos.por_pagina));
  if (totalPaginas <= 1) return;
  const anterior = el('button', { clase: 'boton boton-secundario boton-pequeno', type: 'button', onclick: () => alCambiar(datos.pagina - 1) }, [icono('chevron-left'), 'Anterior']);
  const siguiente = el('button', { clase: 'boton boton-secundario boton-pequeno', type: 'button', onclick: () => alCambiar(datos.pagina + 1) }, ['Siguiente', icono('chevron-right')]);
  anterior.disabled = datos.pagina <= 1;
  siguiente.disabled = datos.pagina >= totalPaginas;
  contenedor.append(anterior, el('span', { texto: `Página ${datos.pagina} de ${totalPaginas}` }), siguiente);
}

// Tarjeta de un objeto (parte PÚBLICA), estilo tarjetas de programas.
function tarjetaObjeto(objeto, enlace) {
  return el('a', { clase: 'tarjeta tarjeta-hover', href: enlace }, [
    el('div', { clase: `portada ${tonoCategoria(objeto.categoria_id)}` }, [
      icono(iconoCategoria(objeto.categoria)),
      insigniaEstado(objeto.estado, objeto.estado_nombre),
    ]),
    el('div', { clase: 'cuerpo' }, [
      el('span', { clase: 'etiqueta-seccion', texto: objeto.categoria }),
      el('h3', { texto: objeto.nombre }),
      el('p', {}, [icono('location-dot'), ' ', objeto.ubicacion]),
      el('div', { clase: 'pie-tarjeta' }, [
        el('span', {}, [icono('calendar'), ' ', formatearFecha(objeto.fecha_evento)]),
        insigniaTipo(objeto.tipo),
      ]),
    ]),
  ]);
}
