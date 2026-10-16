/* ============================================
   LAYOUT.JS
   ============================================
   Arma el encabezado (barra superior + menú) y el pie de página de TODAS
   las páginas, según quién haya iniciado sesión. Así cada HTML no repite
   el mismo bloque y el menú siempre muestra solo lo que ese rol puede usar.

   Cada página declara en <body>:
     data-acceso = publico | invitado | estudiante | encargado | administrador | sesion
     data-menu   = clave del enlace activo del menú (opcional)

   Las páginas usan la promesa global `sesionLista` para empezar:
     sesionLista.then((usuario) => { ... });

   RECORDATORIO: esto es experiencia de usuario. El backend vuelve a
   verificar la sesión y el rol en cada petición.
*/

const MENU_POR_ROL = {
  invitado: [
    { clave: 'inicio', texto: 'Inicio', href: 'index.html' },
    { clave: 'como', texto: '¿Cómo funciona?', href: 'index.html#como-funciona' },
    { clave: 'seguridad', texto: 'Seguridad', href: 'index.html#seguridad' },
    { clave: 'login', texto: 'Ingresar', href: 'login.html' },
  ],
  estudiante: [
    { clave: 'panel', texto: 'Mi panel', href: 'panel-estudiante.html' },
    { clave: 'buscar', texto: 'Buscar objetos', href: 'buscar-objetos.html' },
    { clave: 'reportes', texto: 'Mis reportes', href: 'mis-reportes.html' },
    { clave: 'reclamaciones', texto: 'Mis reclamaciones', href: 'mis-reclamaciones.html' },
  ],
  encargado: [
    { clave: 'panel', texto: 'Panel de la oficina', href: 'panel-encargado.html' },
    { clave: 'objetos', texto: 'Objetos', href: 'encargado-objetos.html' },
    { clave: 'reclamaciones', texto: 'Reclamaciones', href: 'encargado-reclamaciones.html' },
  ],
  administrador: [
    { clave: 'panel', texto: 'Panel', href: 'panel-admin.html' },
    { clave: 'usuarios', texto: 'Usuarios', href: 'admin-usuarios.html' },
    { clave: 'catalogos', texto: 'Catálogos', href: 'admin-catalogos.html' },
    { clave: 'objetos', texto: 'Objetos', href: 'admin-objetos.html' },
    { clave: 'auditoria', texto: 'Auditoría', href: 'admin-auditoria.html' },
  ],
};

const BOTON_POR_ROL = {
  invitado: { texto: 'Crear cuenta', href: 'registro.html', icono: 'user-plus' },
  estudiante: { texto: 'Reportar objeto', href: 'panel-estudiante.html#reportar', icono: 'plus' },
  encargado: { texto: 'Recibir objetos', href: 'encargado-objetos.html?estado=pendiente_entrega', icono: 'box-archive' },
  administrador: null,
};

function _barraSuperior(usuario) {
  const enlacesPerfil = el('div', { clase: 'enlaces-perfil' }, [
    el('a', { href: usuario ? panelDeRol(usuario.rol) : 'login.html' }, [icono('graduation-cap'), 'Soy estudiante']),
    el('a', { href: usuario ? panelDeRol(usuario.rol) : 'login.html' }, [icono('clipboard-check'), 'Soy encargado']),
    el('a', { href: usuario ? panelDeRol(usuario.rol) : 'login.html' }, [icono('user-shield'), 'Soy administrador']),
  ]);

  let derecha;
  if (usuario) {
    const salir = el('a', { href: 'index.html', id: 'enlace-cerrar-sesion' }, [icono('right-from-bracket'), 'Cerrar sesión']);
    salir.addEventListener('click', (evento) => { evento.preventDefault(); cerrarSesion(); });
    derecha = el('div', { clase: 'lado-derecho' }, [
      el('span', { clase: 'solo-escritorio' }, ['Hola, ', el('strong', { texto: usuario.primer_nombre })]),
      el('span', { clase: 'chip-rol', texto: NOMBRE_ROL[usuario.rol] || usuario.rol }),
      salir,
    ]);
  } else {
    derecha = el('div', { clase: 'lado-derecho' }, [
      el('span', { clase: 'solo-escritorio' }, [icono('location-dot'), ' Oficina de objetos perdidos · ', el('strong', { texto: 'Comunidad San Mateo' })]),
    ]);
  }
  return el('div', { clase: 'barra-superior' }, el('div', { clase: 'contenedor' }, [enlacesPerfil, derecha]));
}

function _navegacion(usuario, claveActiva) {
  const rol = usuario ? usuario.rol : 'invitado';
  const menu = el('nav', { clase: 'menu', id: 'menu-principal', 'aria-label': 'Menú principal' });

  (MENU_POR_ROL[rol] || []).forEach((item) => {
    menu.append(el('a', {
      clase: 'enlace-menu' + (item.clave === claveActiva ? ' activo' : ''),
      href: item.href,
      texto: item.texto,
      'aria-current': item.clave === claveActiva ? 'page' : null,
    }));
  });

  if (usuario) {
    const campana = el('a', { clase: 'campana', href: 'notificaciones.html', title: 'Notificaciones', 'aria-label': 'Notificaciones' }, [
      icono('bell'),
      el('span', { clase: 'contador oculto', id: 'contador-notificaciones' }),
    ]);
    menu.append(campana);
  }

  const boton = BOTON_POR_ROL[rol];
  if (boton) {
    menu.append(el('a', { clase: 'boton boton-primario', href: boton.href }, [icono(boton.icono), boton.texto]));
  }

  const botonMovil = el('button', { clase: 'boton-menu-movil', type: 'button', 'aria-label': 'Abrir menú', 'aria-expanded': 'false', 'aria-controls': 'menu-principal' }, icono('bars'));
  botonMovil.addEventListener('click', () => {
    const abierto = menu.classList.toggle('abierto');
    botonMovil.setAttribute('aria-expanded', String(abierto));
  });

  const marca = el('a', { clase: 'marca', href: usuario ? panelDeRol(usuario.rol) : 'index.html' }, [
    el('img', { src: 'img/logo-sanmateo.png', alt: 'Fundación Universitaria San Mateo' }),
    el('span', { clase: 'nombre-app' }, ['Encuentra', el('span', { texto: 'U' }), el('small', { texto: 'Objetos perdidos' })]),
  ]);

  return el('div', { clase: 'navegacion' }, el('div', { clase: 'contenedor' }, [marca, botonMovil, menu]));
}

// Primera columna del pie según el rol (cada uno ve sus propios atajos)
const ENLACES_PIE_POR_ROL = {
  encargado: ['La oficina', [
    ['Objetos por recibir', 'encargado-objetos.html?estado=pendiente_entrega'],
    ['Reclamaciones por revisar', 'encargado-reclamaciones.html'],
    ['Esperando retiro', 'encargado-objetos.html?estado=reservado'],
    ['Todos los reportes', 'encargado-objetos.html'],
  ]],
  administrador: ['Administración', [
    ['Usuarios y roles', 'admin-usuarios.html'],
    ['Catálogos y reglas', 'admin-catalogos.html'],
    ['Auditoría', 'admin-auditoria.html'],
    ['Reportes y exportación', 'admin-objetos.html'],
  ]],
  estudiante: ['Estudiantes', [
    ['Buscar objetos', 'buscar-objetos.html'],
    ['Reportar una pérdida', 'reportar-perdido.html'],
    ['Reportar un hallazgo', 'reportar-encontrado.html'],
    ['Mis reclamaciones', 'mis-reclamaciones.html'],
  ]],
};

function _pie(usuario) {
  const columna = (titulo, enlaces) => el('div', {}, [
    el('h4', { texto: titulo }),
    el('ul', {}, enlaces.map(([texto, href]) => el('li', {}, el('a', { href, texto })))),
  ]);
  const anio = new Date().getFullYear();
  const [tituloRol, enlacesRol] = ENLACES_PIE_POR_ROL[usuario ? usuario.rol : 'estudiante'];
  const enlacesCuenta = usuario
    ? [['Mis avisos', 'notificaciones.html'], ['Mi panel', panelDeRol(usuario.rol)]]
    : [['Iniciar sesión', 'login.html'], ['Crear cuenta', 'registro.html'], ['Recuperar contraseña', 'recuperar-contrasena.html']];

  return el('div', { clase: 'contenedor' }, [
    el('div', { clase: 'columnas' }, [
      el('div', {}, [
        el('img', { clase: 'logo-pie', src: 'img/logo-sanmateo.png', alt: 'Fundación Universitaria San Mateo' }),
        el('p', { clase: 'lema', texto: 'EncuentraU · Objetos perdidos y encontrados' }),
        el('div', {}, [
          el('span', { clase: 'sello' }, [icono('envelope-circle-check'), 'Correo institucional verificado']),
          el('span', { clase: 'sello' }, [icono('user-secret'), 'Verificación a ciegas']),
          el('span', { clase: 'sello' }, [icono('clipboard-list'), 'Auditoría de cambios']),
        ]),
      ]),
      columna(tituloRol, enlacesRol),
      columna('¿Cómo funciona?', [
        ['Los 4 pasos', 'index.html#como-funciona'],
        ['Cómo protegemos tu objeto', 'index.html#seguridad'],
        ['Preguntas frecuentes', 'index.html#preguntas'],
      ]),
      columna('Tu cuenta', enlacesCuenta),
    ]),
    el('div', { clase: 'inferior' }, [
      el('span', { texto: `© ${anio} EncuentraU · Proyecto académico de estudiantes de la Fundación Universitaria San Mateo. No es un canal oficial de la universidad.` }),
      el('span', { texto: 'Flask · PostgreSQL · JavaScript' }),
    ]),
  ]);
}

async function actualizarContadorNotificaciones() {
  const contador = document.getElementById('contador-notificaciones');
  if (!contador) return;
  const resultado = await peticionGet('/notificaciones', { no_leidas: 1 });
  if (!resultado.ok) return;
  const cantidad = resultado.datos.no_leidas || 0;
  contador.textContent = cantidad > 9 ? '9+' : String(cantidad);
  contador.classList.toggle('oculto', cantidad === 0);
}

function _redirigirALogin() {
  const actual = window.location.pathname.split('/').pop() + window.location.search;
  const siguiente = esPaginaInterna(actual) ? `?siguiente=${encodeURIComponent(actual)}` : '';
  window.location.replace(`login.html${siguiente}`);
}

const sesionLista = (async function iniciarLayout() {
  const acceso = document.body.dataset.acceso || 'publico';
  const usuario = await obtenerSesion();

  // Control de acceso de la INTERFAZ (el servidor aplica el control real)
  if (acceso === 'invitado' && usuario) {
    window.location.replace(panelDeRol(usuario.rol));
    return new Promise(() => {});
  }
  if (['estudiante', 'encargado', 'administrador', 'sesion'].includes(acceso)) {
    if (!usuario) {
      _redirigirALogin();
      return new Promise(() => {});
    }
    if (acceso !== 'sesion' && usuario.rol !== acceso) {
      window.location.replace(panelDeRol(usuario.rol));
      return new Promise(() => {});
    }
  }

  const encabezado = document.getElementById('encabezado');
  if (encabezado) encabezado.append(_barraSuperior(usuario), _navegacion(usuario, document.body.dataset.menu));
  const pie = document.getElementById('pie');
  if (pie) {
    pie.classList.add('pie');
    pie.append(_pie(usuario));
  }
  document.body.classList.add('listo');

  if (usuario) actualizarContadorNotificaciones();
  return usuario;
})();
