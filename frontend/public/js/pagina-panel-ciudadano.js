(async function () {
  const usuario = await protegerPagina();
  if (!usuario) return;
  document.getElementById('saludo').textContent = 'Hola, ' + usuario.primer_nombre;
})();
