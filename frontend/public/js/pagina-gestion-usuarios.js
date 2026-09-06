(async function () {
  const yo = await protegerPagina({ admin: true });
  if (!yo) return;

  const ROLES_POSIBLES = ['ciudadano', 'administrador'];
  const cuerpoTabla = document.getElementById('cuerpo-tabla');

  async function cargar() {
    const resultado = await peticionGet('/admin/usuarios?por_pagina=100');
    const usuarios = resultado.datos.datos || [];
    cuerpoTabla.textContent = '';

    if (usuarios.length === 0) {
      const fila = document.createElement('tr');
      const celda = crearElemento('td', 'No hay usuarios.');
      celda.colSpan = 4;
      fila.appendChild(celda);
      cuerpoTabla.appendChild(fila);
      return;
    }

    usuarios.forEach(usuario => {
      const esUnoMismo = usuario.id === yo.id;
      const fila = document.createElement('tr');

      fila.appendChild(crearElemento('td', `${usuario.primer_nombre} ${usuario.primer_apellido}`));
      fila.appendChild(crearElemento('td', usuario.correo));

      const celdaRol = crearElemento('td');
      const selectorRol = document.createElement('select');
      selectorRol.disabled = esUnoMismo;
      ROLES_POSIBLES.forEach(rol => {
        const opcion = crearElemento('option', rol);
        opcion.value = rol;
        if (rol === usuario.rol) opcion.selected = true;
        selectorRol.appendChild(opcion);
      });
      selectorRol.addEventListener('change', async function () {
        const resultadoCambio = await peticionProtegida(`/admin/usuarios/${usuario.id}`, 'PUT', { rol: this.value });
        if (!resultadoCambio.ok) {
          alert(resultadoCambio.datos.mensaje || 'No se pudo cambiar el rol');
          cargar();
        }
      });
      celdaRol.appendChild(selectorRol);
      fila.appendChild(celdaRol);

      const celdaAcciones = crearElemento('td');
      const botonActivo = crearElemento(
        'button',
        usuario.activo ? 'Desactivar' : 'Activar',
        usuario.activo ? 'btn btn-danger btn-small' : 'btn btn-secondary btn-small',
      );
      botonActivo.disabled = esUnoMismo;
      botonActivo.addEventListener('click', async function () {
        const resultadoCambio = await peticionProtegida(`/admin/usuarios/${usuario.id}`, 'PUT', {
          activo: !usuario.activo,
        });
        if (!resultadoCambio.ok) {
          alert(resultadoCambio.datos.mensaje || 'No se pudo actualizar el usuario');
        }
        cargar();
      });
      celdaAcciones.appendChild(botonActivo);
      fila.appendChild(celdaAcciones);

      cuerpoTabla.appendChild(fila);
    });
  }

  cargar();
})();
