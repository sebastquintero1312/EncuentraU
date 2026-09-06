/* ============================================
   DATOS TEMPORALES - EncuentraU
   ============================================
   IMPORTANTE: estos datos son SIMULADOS y solo existen en memoria
   del navegador. NO hay ninguna base de datos ni backend real conectado.
   Si recargas la página, cualquier cambio hecho aquí se pierde.
   Esto se reemplazará por peticiones reales a la API en una fase futura.
*/

const usuariosSimulados = [
  { id: 1, nombre: 'Laura Gómez', correo: '[email protected]', rol: 'ciudadano' },
  { id: 2, nombre: 'Carlos Ruiz', correo: '[email protected]', rol: 'ciudadano' },
  { id: 3, nombre: 'Admin EncuentraU', correo: '[email protected]', rol: 'administrador' }
];

// Simulamos que el usuario que inició sesión es Laura Gómez (id 1)
const usuarioActualId = 1;

const reportesSimulados = [
  {
    id: 1,
    tipo: 'perdido',
    objeto: 'Mochila azul',
    categoria: 'Accesorios',
    descripcion: 'Mochila azul marca Totto, tenía una laptop y un cuaderno adentro.',
    ubicacion: 'Biblioteca central',
    fecha: '2026-08-20',
    estado: 'activo',
    usuarioId: 1,
    usuarioNombre: 'Laura Gómez'
  },
  {
    id: 2,
    tipo: 'encontrado',
    objeto: 'Celular Samsung',
    categoria: 'Tecnología',
    descripcion: 'Celular Samsung negro, encontrado con la pantalla un poco rayada.',
    ubicacion: 'Cafetería bloque 4',
    fecha: '2026-08-21',
    estado: 'en proceso',
    usuarioId: 2,
    usuarioNombre: 'Carlos Ruiz'
  },
  {
    id: 3,
    tipo: 'perdido',
    objeto: 'Cuaderno de apuntes',
    categoria: 'Útiles',
    descripcion: 'Cuaderno rojo de Cálculo II con el nombre en la portada.',
    ubicacion: 'Salón 305',
    fecha: '2026-08-18',
    estado: 'resuelto',
    usuarioId: 1,
    usuarioNombre: 'Laura Gómez'
  },
  {
    id: 4,
    tipo: 'encontrado',
    objeto: 'Llaves con llavero verde',
    categoria: 'Accesorios',
    descripcion: 'Juego de llaves con un llavero verde en forma de pelota.',
    ubicacion: 'Parqueadero norte',
    fecha: '2026-08-23',
    estado: 'activo',
    usuarioId: 2,
    usuarioNombre: 'Carlos Ruiz'
  },
  {
    id: 5,
    tipo: 'perdido',
    objeto: 'Audífonos inalámbricos',
    categoria: 'Tecnología',
    descripcion: 'Audífonos blancos, se perdieron en el gimnasio de la universidad.',
    ubicacion: 'Gimnasio',
    fecha: '2026-08-25',
    estado: 'cerrado',
    usuarioId: 1,
    usuarioNombre: 'Laura Gómez'
  }
];

const solicitudesSimuladas = [
  {
    id: 1,
    reporteId: 2,
    usuarioId: 1,
    mensaje: 'Ese celular es mío, tiene una funda transparente que no se ve en la foto.',
    fecha: '2026-08-22',
    estado: 'pendiente'
  }
];
