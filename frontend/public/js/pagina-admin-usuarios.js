/* Gestión de usuarios. El backend aplica las reglas (whitelist de campos,
   no se crean administradores desde la web, un admin no se modifica a sí
   mismo); la interfaz solo ofrece las opciones permitidas. */

const filtrosUsuarios = { q: '', rol: '', marcados: '', pagina: 1 };
let usuarioActualAdmin = null;

async function actualizarUsuario(usuario, cambios) {
  const mensaje = document.getElementById('mensaje');
  const resultado = await peticionProtegida(`/admin/usuarios/${encodeURIComponent(usuario.id)}`, 'PUT', cambios);
  mostrarMensaje(mensaje, resultado.ok ? 'exito' : 'error', resultado.ok ? resultado.datos.mensaje : mensajeDeError(resultado));
  cargarUsuarios();
}

function accionesUsuario(usuario) {
  const acciones = el('div', { clase: 'acciones-tabla' });
  const esYo = usuarioActualAdmin && usuario.id === usuarioActualAdmin.id;
  if (usuario.rol === 'administrador' || esYo) {
    acciones.append(el('span', { clase: 'texto-suave texto-pequeno', texto: esYo ? 'Tu cuenta' : 'Solo desde la terminal' }));
    return acciones;
  }

  if (usuario.rol === 'estudiante') {
    const nombrar = el('button', { clase: 'boton boton-secundario boton-pequeno', type: 'button' }, [icono('clipboard-check'), 'Nombrar encargado']);
    nombrar.disabled = !usuario.correo_verificado;
    if (!usuario.correo_verificado) nombrar.title = 'Primero debe verificar su correo';
    nombrar.addEventListener('click', () => {
      if (window.confirm(`¿Nombrar a ${usuario.nombre_completo} como encargado de la oficina?`)) actualizarUsuario(usuario, { rol: 'encargado' });
    });
    acciones.append(nombrar);
  } else if (usuario.rol === 'encargado') {
    const quitar = el('button', { clase: 'boton boton-secundario boton-pequeno', type: 'button' }, [icono('user-graduate'), 'Volver a estudiante']);
    quitar.addEventListener('click', () => {
      if (window.confirm(`¿Quitarle a ${usuario.nombre_completo} el rol de encargado?`)) actualizarUsuario(usuario, { rol: 'estudiante' });
    });
    acciones.append(quitar);
  }

  const activar = el('button', { clase: `boton ${usuario.activo ? 'boton-peligro' : 'boton-exito'} boton-pequeno`, type: 'button' },
    [icono(usuario.activo ? 'user-slash' : 'user-check'), usuario.activo ? 'Desactivar' : 'Activar']);
  activar.addEventListener('click', () => {
    const pregunta = usuario.activo ? `¿Desactivar la cuenta de ${usuario.nombre_completo}? No podrá iniciar sesión.` : `¿Reactivar la cuenta de ${usuario.nombre_completo}?`;
    if (window.confirm(pregunta)) actualizarUsuario(usuario, { activo: !usuario.activo });
  });
  acciones.append(activar);

  if (usuario.marcado_revision) {
    const levantar = el('button', { clase: 'boton boton-primario boton-pequeno', type: 'button' }, [icono('flag-checkered'), 'Quitar revisión']);
    levantar.addEventListener('click', async () => {
      if (!window.confirm('¿Revisaste el caso y quieres permitirle volver a reclamar objetos?')) return;
      const resultado = await peticionProtegida(`/admin/usuarios/${encodeURIComponent(usuario.id)}/quitar-revision`, 'POST');
      mostrarMensaje(document.getElementById('mensaje'), resultado.ok ? 'exito' : 'error', resultado.datos.mensaje);
      cargarUsuarios();
    });
    acciones.append(levantar);
  }
  return acciones;
}

async function cargarUsuarios() {
  const cuerpo = document.getElementById('cuerpo-tabla');
  vaciar(cuerpo);
  cuerpo.append(el('tr', {}, el('td', { colspan: '5' }, estadoCargando())));
  const resultado = await peticionGet('/admin/usuarios', { ...filtrosUsuarios, por_pagina: 15 });
  vaciar(cuerpo);
  if (!resultado.ok) {
    cuerpo.append(el('tr', {}, el('td', { colspan: '5' }, el('div', { clase: 'alerta alerta-error', texto: resultado.datos.mensaje }))));
    return;
  }
  if (!resultado.datos.datos.length) {
    cuerpo.append(el('tr', {}, el('td', { colspan: '5' }, estadoVacio('No hay usuarios con estos filtros.', 'users'))));
  }
  resultado.datos.datos.forEach((usuario) => cuerpo.append(el('tr', {}, [
    el('td', {}, [
      el('strong', { texto: usuario.nombre_completo }),
      el('div', { clase: 'texto-suave texto-pequeno', texto: usuario.correo }),
      usuario.marcado_revision ? el('span', { clase: 'insignia insignia-rojo', title: usuario.motivo_revision }, [icono('flag'), 'En revisión']) : null,
    ]),
    el('td', {}, el('span', { clase: 'insignia insignia-oscura', texto: NOMBRE_ROL[usuario.rol] })),
    el('td', {}, usuario.correo_verificado
      ? el('span', { clase: 'insignia insignia-verde' }, [icono('check'), 'Sí'])
      : el('span', { clase: 'insignia insignia-ambar', texto: 'Pendiente' })),
    el('td', {}, usuario.activo ? el('span', { clase: 'insignia insignia-verde', texto: 'Activa' }) : el('span', { clase: 'insignia insignia-gris', texto: 'Desactivada' })),
    el('td', {}, accionesUsuario(usuario)),
  ])));
  pintarPaginacion(document.getElementById('paginacion'), resultado.datos, (pagina) => { filtrosUsuarios.pagina = pagina; cargarUsuarios(); });
}

sesionLista.then((usuario) => {
  usuarioActualAdmin = usuario;
  const soloMarcados = document.getElementById('solo-marcados');
  if (parametroUrl('marcados')) { filtrosUsuarios.marcados = '1'; soloMarcados.checked = true; }

  document.querySelectorAll('#pildoras-rol .pildora').forEach((pildora) => {
    pildora.addEventListener('click', () => {
      document.querySelectorAll('#pildoras-rol .pildora').forEach((p) => p.classList.remove('activa'));
      pildora.classList.add('activa');
      filtrosUsuarios.rol = pildora.dataset.rol;
      filtrosUsuarios.pagina = 1;
      cargarUsuarios();
    });
  });
  soloMarcados.addEventListener('change', () => { filtrosUsuarios.marcados = soloMarcados.checked ? '1' : ''; filtrosUsuarios.pagina = 1; cargarUsuarios(); });
  let espera = null;
  document.getElementById('texto').addEventListener('input', (evento) => {
    clearTimeout(espera);
    espera = setTimeout(() => { filtrosUsuarios.q = evento.target.value.trim(); filtrosUsuarios.pagina = 1; cargarUsuarios(); }, 350);
  });
  cargarUsuarios();
});
