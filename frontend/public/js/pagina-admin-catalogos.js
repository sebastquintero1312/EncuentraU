/* Administración de categorías, ubicaciones y parámetros. */

function avisar(resultado) {
  mostrarMensaje(document.getElementById('mensaje'), resultado.ok ? 'exito' : 'error',
    resultado.ok ? resultado.datos.mensaje : mensajeDeError(resultado));
}

function itemCatalogo(registro, ruta, recargar) {
  const nombre = el('input', { type: 'text', value: registro.nombre, maxlength: ruta === 'categorias' ? 50 : 80, 'aria-label': 'Nombre' });
  const guardar = el('button', { clase: 'boton boton-secundario boton-pequeno', type: 'button', title: 'Guardar nombre' }, icono('floppy-disk'));
  guardar.addEventListener('click', async () => {
    avisar(await peticionProtegida(`/admin/${ruta}/${encodeURIComponent(registro.id)}`, 'PUT', { nombre: nombre.value.trim() }));
    recargar();
  });
  const alternar = el('button', { clase: `boton ${registro.activa ? 'boton-peligro' : 'boton-exito'} boton-pequeno`, type: 'button' },
    registro.activa ? 'Desactivar' : 'Activar');
  alternar.addEventListener('click', async () => {
    avisar(await peticionProtegida(`/admin/${ruta}/${encodeURIComponent(registro.id)}`, 'PUT', { activa: !registro.activa }));
    recargar();
  });
  return el('li', { clase: 'item' }, [
    el('div', { clase: 'principal grupo-botones' }, [nombre, registro.activa ? null : el('span', { clase: 'insignia insignia-gris', texto: 'Inactiva' })]),
    el('div', { clase: 'grupo-botones' }, [guardar, alternar]),
  ]);
}

async function cargarCatalogo(ruta, idLista) {
  const lista = document.getElementById(idLista);
  vaciar(lista);
  const resultado = await peticionGet(`/admin/${ruta}`);
  if (!resultado.ok) { avisar(resultado); return; }
  resultado.datos.datos.forEach((registro) => lista.append(itemCatalogo(registro, ruta, () => cargarCatalogo(ruta, idLista))));
}

async function cargarParametros() {
  const cuerpo = document.getElementById('tabla-parametros');
  vaciar(cuerpo);
  const resultado = await peticionGet('/admin/parametros');
  if (!resultado.ok) { avisar(resultado); return; }
  resultado.datos.datos.forEach((parametro) => {
    const valor = el('input', { type: 'number', value: parametro.valor, min: parametro.minimo, max: parametro.maximo, 'aria-label': parametro.descripcion });
    const guardar = el('button', { clase: 'boton boton-secundario boton-pequeno', type: 'button' }, [icono('floppy-disk'), 'Guardar']);
    guardar.addEventListener('click', async () => {
      avisar(await peticionProtegida(`/admin/parametros/${encodeURIComponent(parametro.clave)}`, 'PUT', { valor: Number(valor.value) }));
      cargarParametros();
    });
    cuerpo.append(el('tr', {}, [
      el('td', {}, [el('strong', { texto: parametro.descripcion }), el('div', { clase: 'texto-suave texto-pequeno', texto: parametro.clave })]),
      el('td', { texto: `${parametro.minimo} a ${parametro.maximo}` }),
      el('td', {}, valor),
      el('td', {}, guardar),
    ]));
  });
}

function conectarFormularioNuevo(idFormulario, idCampo, ruta, idLista) {
  document.getElementById(idFormulario).addEventListener('submit', async (evento) => {
    evento.preventDefault();
    const campo = document.getElementById(idCampo);
    if (campo.value.trim().length < 3) {
      mostrarMensaje(document.getElementById('mensaje'), 'error', 'El nombre debe tener al menos 3 caracteres');
      return;
    }
    const resultado = await peticionSegura(`/admin/${ruta}`, { nombre: campo.value.trim() });
    avisar(resultado);
    if (resultado.ok) campo.value = '';
    cargarCatalogo(ruta, idLista);
  });
}

sesionLista.then(() => {
  conectarFormularioNuevo('form-categoria', 'nueva-categoria', 'categorias', 'lista-categorias');
  conectarFormularioNuevo('form-ubicacion', 'nueva-ubicacion', 'ubicaciones', 'lista-ubicaciones');
  cargarCatalogo('categorias', 'lista-categorias');
  cargarCatalogo('ubicaciones', 'lista-ubicaciones');
  cargarParametros();
});
