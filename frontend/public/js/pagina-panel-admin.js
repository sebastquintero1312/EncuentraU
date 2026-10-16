/* Panel del administrador: indicadores, actividad mensual, cuentas en
   revisión y trabajo de los encargados (vistas de PostgreSQL). */

const NOMBRE_MES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

function pintarBarras(mensuales) {
  const contenedor = document.getElementById('barras-mensuales');
  if (!mensuales.length) {
    contenedor.append(estadoVacio('Todavía no hay actividad.', 'chart-column'));
    return;
  }
  const maximo = Math.max(1, ...mensuales.map((m) => m.perdidos + m.encontrados + m.entregados));
  mensuales.forEach((mes) => {
    const [anio, numeroMes] = mes.mes.split('-');
    const barra = el('div', { clase: 'barra-fondo', title: `Perdidos ${mes.perdidos} · Encontrados ${mes.encontrados} · Entregados ${mes.entregados}` });
    [['perdidos', mes.perdidos], ['encontrados', mes.encontrados], ['entregados', mes.entregados]].forEach(([clase, valor]) => {
      const relleno = el('div', { clase: `barra-relleno ${clase}` });
      relleno.style.width = `${(valor / maximo) * 100}%`;
      barra.append(relleno);
    });
    contenedor.append(el('div', { clase: 'barra-fila' }, [
      el('span', { texto: `${NOMBRE_MES[Number(numeroMes) - 1]} ${anio}` }),
      barra,
      el('strong', { texto: String(mes.perdidos + mes.encontrados + mes.entregados) }),
    ]));
  });
}

function pintarEncargados(encargados) {
  const cuerpo = document.getElementById('tabla-encargados');
  if (!encargados.length) {
    cuerpo.append(el('tr', {}, el('td', { colspan: '6' }, estadoVacio('Aún no hay encargados. Nómbralos desde Usuarios.', 'user-plus'))));
    return;
  }
  encargados.forEach((e) => cuerpo.append(el('tr', {}, [
    el('td', {}, [
      el('strong', { texto: e.encargado }),
      el('div', { clase: 'texto-suave texto-pequeno', texto: e.correo }),
      e.rol !== 'encargado' ? el('span', { clase: 'insignia insignia-gris', texto: 'Ya no es encargado' }) : null,
    ]),
    el('td', { texto: String(e.objetos_recibidos) }),
    el('td', { texto: String(e.preaprobaciones) }),
    el('td', { texto: String(e.rechazos) }),
    el('td', { texto: String(e.entregas) }),
    el('td', { texto: e.horas_promedio_custodia === null ? '—' : `${e.horas_promedio_custodia} h` }),
  ])));
}

sesionLista.then(async () => {
  const [estadisticas, marcados] = await Promise.all([
    peticionGet('/admin/estadisticas'),
    peticionGet('/admin/usuarios', { marcados: 1, por_pagina: 5 }),
  ]);
  if (estadisticas.ok) {
    const g = estadisticas.datos.generales;
    document.getElementById('kpi-custodia').textContent = g.en_custodia;
    document.getElementById('kpi-entregados').textContent = g.entregados;
    document.getElementById('kpi-reclamaciones').textContent = g.reclamaciones_pendientes;
    document.getElementById('kpi-revision').textContent = g.cuentas_en_revision;
    pintarBarras(estadisticas.datos.mensuales);
    pintarEncargados(estadisticas.datos.encargados);
  }
  const lista = document.getElementById('lista-marcados');
  if (marcados.ok && marcados.datos.datos.length) {
    lista.append(el('ul', { clase: 'lista-items' }, marcados.datos.datos.map((u) => el('li', { clase: 'item' }, [
      el('div', { clase: 'principal' }, [
        el('h4', { texto: u.nombre_completo }),
        el('div', { clase: 'meta' }, [el('span', { texto: u.correo }), el('span', { texto: u.motivo_revision })]),
      ]),
      el('a', { clase: 'boton boton-secundario boton-pequeno', href: `admin-auditoria.html?tabla=solicitudes&usuario_id=${encodeURIComponent(u.id)}` }, ['Historial', icono('arrow-right')]),
    ]))));
  } else {
    lista.append(estadoVacio('No hay cuentas en revisión.', 'circle-check'));
  }
});
