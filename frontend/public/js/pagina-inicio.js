/* Página de inicio: cifras públicas y botones según la sesión. */

sesionLista.then(async (usuario) => {
  if (usuario) {
    const acciones = document.getElementById('acciones-hero');
    vaciar(acciones);
    acciones.append(el('a', { clase: 'boton boton-primario', href: panelDeRol(usuario.rol) }, [icono('arrow-right'), 'Ir a mi panel']));
  }

  const resultado = await peticionGet('/estadisticas/publicas');
  if (resultado.ok) {
    document.getElementById('cifra-custodia').textContent = resultado.datos.en_custodia;
    document.getElementById('cifra-entregados').textContent = resultado.datos.entregados;
  }
});
