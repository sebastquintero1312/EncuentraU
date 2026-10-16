"""Verificación de extremo a extremo con un navegador REAL (Playwright).

A diferencia de pytest (que usa el test client de Flask), este script
levanta el servidor de verdad, abre un navegador y hace clic/escribe como
lo haría una persona, con los TRES roles:

  estudiante que encuentra · estudiante dueño · encargado · administrador

Recorre el flujo completo (registro con verificación de correo, reporte,
recepción en la oficina, reclamación a ciegas, pre-aprobación, código de
retiro, entrega presencial, auditoría) y comprueba que no haya errores de
JavaScript ni bloqueos de la política CSP. Además guarda capturas de
pantalla en docs/evidencia/capturas_v2/.

Requisitos:
  * Base de datos de desarrollo ya migrada (flask db upgrade).
  * Variables DATABASE_URL / DATABASE_URL_MIGRACIONES (en backend/.env o en
    el entorno).
  * Playwright (requirements-dev.txt). Usa el navegador Edge o Chrome
    instalado; si no hay ninguno: `playwright install chromium`.

Uso (desde backend/):
    venv\\Scripts\\python.exe tests\\e2e\\verificacion_navegador.py

Los correos se toman de la salida del servidor (CORREO_PROVEEDOR=consola).
Cada ejecución usa correos nuevos, así que se puede repetir.
"""

import os
import re
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

DIRECTORIO_BACKEND = Path(__file__).resolve().parents[2]
CARPETA_CAPTURAS = DIRECTORIO_BACKEND.parent / 'docs' / 'evidencia' / 'capturas_v2'
ARCHIVO_LOG = DIRECTORIO_BACKEND / 'instance' / 'e2e_servidor.log'
BASE = 'http://127.0.0.1:5000'
CONTRASENA = 'ClaveSegura!2026x'
SUFIJO = str(int(time.time()))[-6:]
FALLOS = []
ERRORES_NAVEGADOR = []
RESPUESTAS_ESPERADAS = []


def revisar(nombre, condicion):
    print(f"[{'OK' if condicion else 'FALLO'}] {nombre}", flush=True)
    if not condicion:
        FALLOS.append(nombre)


def correo(nombre):
    return f'{nombre}.e2e{SUFIJO}@sanmateo.edu.co'


# ---------------------------------------------------------------------------
# Servidor y correos
# ---------------------------------------------------------------------------

def iniciar_servidor():
    ARCHIVO_LOG.parent.mkdir(exist_ok=True)
    entorno = dict(os.environ, FLASK_ENV='e2e', CORREO_PROVEEDOR='consola', URL_PUBLICA=BASE, PYTHONUNBUFFERED='1')
    entorno.pop('PORT', None)
    salida = open(ARCHIVO_LOG, 'w', encoding='utf-8')
    proceso = subprocess.Popen([sys.executable, 'app.py'], cwd=DIRECTORIO_BACKEND, env=entorno,
                               stdout=salida, stderr=subprocess.STDOUT)
    import urllib.request
    for _ in range(60):
        try:
            urllib.request.urlopen(f'{BASE}/health', timeout=1)
            return proceso
        except OSError:
            time.sleep(0.5)
    proceso.kill()
    sys.exit('El servidor no arrancó. Revisa ' + str(ARCHIVO_LOG))


def token_del_correo(destinatario, pagina, intentos=40):
    patron = re.compile(rf'Correo para {re.escape(destinatario)} =====.*?{re.escape(pagina)}\?token=([A-Za-z0-9_\-]+)', re.S)
    for _ in range(intentos):
        coincidencias = patron.findall(ARCHIVO_LOG.read_text(encoding='utf-8', errors='replace'))
        if coincidencias:
            return coincidencias[-1]
        time.sleep(0.25)
    return None


def flask_cli(*argumentos):
    entorno = dict(os.environ, FLASK_APP='app.py', FLASK_ENV='e2e')
    return subprocess.run([sys.executable, '-m', 'flask', *argumentos], cwd=DIRECTORIO_BACKEND, env=entorno,
                          capture_output=True, text=True)


# ---------------------------------------------------------------------------
# Navegador
# ---------------------------------------------------------------------------

def nueva_pagina(navegador, etiqueta, movil=False):
    opciones = {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True} if movil else {'viewport': {'width': 1366, 'height': 900}}
    pagina = navegador.new_context(**opciones).new_page()
    # "Failed to load resource" = una respuesta 4xx de la API que la página
    # maneja a propósito (ej. 403 al entrar sin verificar el correo). Se
    # anotan aparte; los errores reales son excepciones de JavaScript y
    # violaciones de la política CSP.
    pagina.on('console', lambda m: (RESPUESTAS_ESPERADAS if 'Failed to load resource' in m.text else ERRORES_NAVEGADOR)
              .append(f'{etiqueta}: {m.text}') if m.type == 'error' else None)
    pagina.on('pageerror', lambda exc: ERRORES_NAVEGADOR.append(f'{etiqueta}: {exc}'))
    pagina.on('dialog', lambda dialogo: dialogo.accept())  # confirmaciones (window.confirm)
    return pagina


def captura(pagina, nombre):
    CARPETA_CAPTURAS.mkdir(parents=True, exist_ok=True)
    pagina.screenshot(path=str(CARPETA_CAPTURAS / f'{nombre}.png'), full_page=True)


def registrar_y_verificar(pagina, nombre, apellido, direccion):
    pagina.goto(f'{BASE}/registro.html')
    pagina.fill('#primerNombre', nombre)
    pagina.fill('#primerApellido', apellido)
    pagina.fill('#correo', direccion)
    pagina.fill('#contrasena', CONTRASENA)
    pagina.fill('#confirmar', CONTRASENA)
    pagina.click('#boton-registro')
    pagina.wait_for_selector('#registro-exitoso:not(.oculto)', timeout=8000)
    token = token_del_correo(direccion, 'verificar-correo.html')
    pagina.goto(f'{BASE}/verificar-correo.html?token={token}')
    pagina.wait_for_selector('#verificacion-exitosa:not(.oculto)', timeout=8000)
    return token


def iniciar_sesion(pagina, direccion, panel):
    pagina.goto(f'{BASE}/login.html')
    pagina.fill('#correo', direccion)
    pagina.fill('#contrasena', CONTRASENA)
    pagina.click('#boton-entrar')
    pagina.wait_for_url(f'**/{panel}', timeout=8000)


def reportar(pagina, tipo, nombre, descripcion):
    pagina.goto(f'{BASE}/reportar-{tipo}.html')
    pagina.wait_for_selector('#categoria option:nth-child(2)', state='attached')
    pagina.fill('#nombre', nombre)
    pagina.select_option('#categoria', label='Tecnología')
    pagina.select_option('#ubicacion', label='Biblioteca')
    pagina.fill('#detalle-ubicacion', 'Segundo piso')
    pagina.fill('#fecha', date.today().isoformat())
    pagina.fill('#descripcion', descripcion)
    pagina.click('#boton-guardar')
    pagina.wait_for_url('**/detalle-objeto.html?id=*', timeout=8000)
    pagina.wait_for_selector('#panel-datos .datos')
    return int(re.search(r'id=(\d+)', pagina.url).group(1))


def main():
    servidor = iniciar_servidor()
    try:
        with sync_playwright() as p:
            try:
                navegador = p.chromium.launch(channel='msedge')
            except Exception:  # noqa: BLE001
                navegador = p.chromium.launch(channel='chrome')

            # --- Público -------------------------------------------------------
            visitante = nueva_pagina(navegador, 'visitante')
            visitante.goto(f'{BASE}/')
            visitante.wait_for_selector('.pie .columnas')
            # (wait_for_function no sirve aquí: evalúa texto como JavaScript y la
            # política CSP de la página lo bloquea, como debe ser)
            for _ in range(40):
                if visitante.text_content('#cifra-custodia').strip().isdigit():
                    break
                time.sleep(0.25)
            revisar('Inicio carga con encabezado y pie generados por layout.js', visitante.locator('.navegacion .marca').count() == 1)
            revisar('Inicio muestra las cifras públicas', visitante.text_content('#cifra-custodia').strip().isdigit())
            captura(visitante, '01_inicio')
            visitante.goto(f'{BASE}/panel-admin.html')
            visitante.wait_for_url('**/login.html*', timeout=8000)
            revisar('Una página protegida sin sesión redirige al login', 'login.html' in visitante.url)
            captura(visitante, '02_login')

            # --- Registro con verificación del correo -------------------------
            ana = nueva_pagina(navegador, 'ana (encuentra)')
            ana.goto(f'{BASE}/registro.html')
            ana.fill('#correo', 'alguien@gmail.com')
            ana.click('#boton-registro')
            revisar('El registro rechaza correos que no son institucionales', 'institucional' in ana.text_content('#form-registro'))
            captura(ana, '03_registro')

            ana.goto(f'{BASE}/registro.html')
            ana.fill('#primerNombre', 'Ana')
            ana.fill('#primerApellido', 'Acosta')
            ana.fill('#correo', correo('ana'))
            ana.fill('#contrasena', CONTRASENA)
            ana.fill('#confirmar', CONTRASENA)
            ana.click('#boton-registro')
            ana.wait_for_selector('#registro-exitoso:not(.oculto)')
            ana.goto(f'{BASE}/login.html')
            ana.fill('#correo', correo('ana'))
            ana.fill('#contrasena', CONTRASENA)
            ana.click('#boton-entrar')
            ana.wait_for_selector('#bloque-reenvio:not(.oculto)')
            revisar('Sin verificar el correo no se puede entrar (y se ofrece reenviar)', 'confirmar tu correo' in ana.text_content('#mensaje'))
            token = token_del_correo(correo('ana'), 'verificar-correo.html')
            revisar('El enlace de verificación llegó por correo', bool(token))
            ana.goto(f'{BASE}/verificar-correo.html?token={token}')
            ana.wait_for_selector('#verificacion-exitosa:not(.oculto)')
            revisar('La verificación quita el token de la barra de direcciones', 'token=' not in ana.url)
            iniciar_sesion(ana, correo('ana'), 'panel-estudiante.html')
            revisar('El panel del estudiante saluda por su nombre', ana.text_content('#nombre-estudiante') == 'Ana')

            beto = nueva_pagina(navegador, 'beto (dueño)')
            registrar_y_verificar(beto, 'Beto', 'Bernal', correo('beto'))
            # Open redirect: un enlace manipulado no debe mandar al usuario a
            # otro sitio después de iniciar sesión.
            beto.goto(f'{BASE}/login.html?siguiente=https%3A%2F%2Fsitio-malicioso.example%2Ffalso.html')
            beto.fill('#correo', correo('beto'))
            beto.fill('#contrasena', CONTRASENA)
            beto.click('#boton-entrar')
            beto.wait_for_url('**/panel-estudiante.html', timeout=8000)
            revisar('El parámetro "siguiente" no redirige a sitios externos (open redirect)', beto.url.startswith(BASE))
            captura(beto, '04_panel_estudiante')

            # --- Administrador (solo desde la terminal) y nombramiento de encargado
            admin = nueva_pagina(navegador, 'admin')
            registrar_y_verificar(admin, 'Adriana', 'Admin', correo('admin'))
            resultado_cli = flask_cli('crear-admin', correo('admin'))
            revisar('flask crear-admin promueve a un usuario verificado', 'promovido a administrador' in resultado_cli.stdout)
            iniciar_sesion(admin, correo('admin'), 'panel-admin.html')

            elena = nueva_pagina(navegador, 'elena (encargada)')
            registrar_y_verificar(elena, 'Elena', 'Encargada', correo('elena'))
            admin.goto(f'{BASE}/admin-usuarios.html')
            admin.fill('#texto', correo('elena'))
            fila = admin.locator('#cuerpo-tabla tr', has_text=correo('elena'))
            fila.locator('button', has_text='Nombrar encargado').click()
            admin.wait_for_selector('#mensaje.alerta-exito')
            revisar('El administrador nombra encargada desde la web', 'Encargado' in admin.locator('#cuerpo-tabla tr', has_text=correo('elena')).text_content())
            captura(admin, '05_admin_usuarios')
            iniciar_sesion(elena, correo('elena'), 'panel-encargado.html')

            # --- Reportes -------------------------------------------------------
            descripcion_privada = 'Samsung A54 negro con funda de Pokemon Pikachu y fondo de pantalla de un perro'
            perdido_id = reportar(beto, 'perdido', 'Celular', 'Samsung negro, funda de Pikachu, fondo de pantalla con mi perro Toby')
            revisar('El dueño ve su descripción privada', 'Pikachu' in beto.text_content('#panel-datos'))
            encontrado_id = reportar(ana, 'encontrado', 'Celular', descripcion_privada)
            revisar('El objeto encontrado queda pendiente de entrega', 'Pendiente de entrega' in ana.text_content('#panel-datos'))
            captura(ana, '06_reporte_encontrado')

            beto.goto(f'{BASE}/buscar-objetos.html')
            beto.wait_for_selector('#resumen-resultados:has-text("objeto")')
            revisar('Lo que aún no está en la oficina no aparece en la búsqueda',
                    beto.locator(f'#resultados a[href="detalle-objeto.html?id={encontrado_id}"]').count() == 0)

            # --- Recepción en la oficina ----------------------------------------
            elena.goto(f'{BASE}/panel-encargado.html')
            elena.wait_for_selector('#lista-pendientes .item, #lista-pendientes .vacio')
            captura(elena, '07_panel_encargado')
            elena.goto(f'{BASE}/oficina-objeto.html?id={encontrado_id}#recepcion')
            elena.wait_for_selector('#recepcion')
            revisar('El encargado ve la descripción privada', 'Pikachu' in elena.text_content('#panel-datos'))
            elena.fill('#campo-observaciones', 'Guardado en el estante B')
            elena.click('#recepcion button[type=submit]')
            elena.wait_for_selector('#panel-datos:has-text("En la oficina")')
            revisar('La recepción deja el objeto en la oficina', 'En la oficina' in elena.text_content('#panel-datos'))

            # --- Búsqueda y reclamación a ciegas --------------------------------
            beto.goto(f'{BASE}/notificaciones.html')
            beto.wait_for_selector('#lista-notificaciones .item')
            revisar('Beto recibe el aviso de posible coincidencia', 'podría ser tuyo' in beto.text_content('#lista-notificaciones'))
            beto.goto(f'{BASE}/buscar-objetos.html')
            tarjeta = beto.locator(f'#resultados a[href="detalle-objeto.html?id={encontrado_id}"]')
            tarjeta.wait_for()
            revisar('El objeto aparece en la búsqueda al llegar a la oficina', tarjeta.count() == 1)
            revisar('La búsqueda NO muestra la descripción privada', 'Pikachu' not in beto.text_content('#resultados'))
            captura(beto, '08_buscar_objetos')
            tarjeta.click()
            beto.wait_for_selector('#panel-acciones a.boton-primario')
            revisar('El detalle público tampoco muestra la descripción privada', 'Pikachu' not in beto.text_content('main'))
            captura(beto, '09_detalle_publico')
            beto.click('#panel-acciones a.boton-primario')
            beto.wait_for_selector('#reporte-perdida option:nth-child(2)', state='attached')
            beto.fill('#descripcion', 'Samsung negro con funda de Pikachu; el fondo de pantalla es mi perro Toby')
            beto.fill('#lugar', 'Biblioteca, segundo piso')
            beto.select_option('#reporte-perdida', str(perdido_id))
            beto.fill('#evidencia', 'Lo desbloqueo con mi huella')
            beto.click('#boton-enviar')
            revisar('Sin aceptar la declaración no se envía', 'aceptar la declaración' in beto.text_content('#error-declaracion'))
            beto.check('#declaracion')
            captura(beto, '10_reclamar')
            beto.click('#boton-enviar')
            beto.wait_for_url('**/mis-reclamaciones.html*')
            beto.wait_for_selector('#lista-reclamaciones article')
            revisar('La reclamación queda pendiente', 'Pendiente' in beto.text_content('#lista-reclamaciones'))

            # --- Revisión del encargado ------------------------------------------
            elena.goto(f'{BASE}/encargado-reclamaciones.html')
            elena.locator('#lista-reclamaciones a', has_text='Revisar').first.click()
            elena.wait_for_selector('#columna-oficina h4')
            revisar('La comparación muestra lo que dijo el estudiante', 'Toby' in elena.text_content('#columna-estudiante'))
            revisar('La comparación muestra los detalles privados', 'Pikachu' in elena.text_content('#columna-oficina'))
            revisar('Se marca la evidencia del reporte de pérdida previo', 'antes' in elena.text_content('#evidencias').lower())
            captura(elena, '11_comparacion_a_ciegas')
            elena.click('#boton-preaprobar')
            elena.wait_for_selector('#cabecera-reclamacion:has-text("Pre-aprobada")')

            # --- Código de retiro y entrega presencial ----------------------------
            beto.goto(f'{BASE}/mis-reclamaciones.html')
            beto.locator('button', has_text='Generar código de retiro').click()
            beto.wait_for_selector('#modal-codigo:not(.oculto)')
            codigo = beto.text_content('#codigo-retiro').strip()
            revisar('El código de retiro tiene 6 dígitos', bool(re.fullmatch(r'\d{6}', codigo)))
            captura(beto, '12_codigo_retiro')
            beto.click('#cerrar-modal-codigo')

            elena.goto(f'{BASE}/oficina-objeto.html?id={encontrado_id}#entrega')
            elena.wait_for_selector('#entrega')
            incorrecto = '000000' if codigo != '000000' else '111111'
            elena.fill('#campo-codigo', incorrecto)
            elena.check('#entrega input[name=carne_verificado]')
            elena.fill('#campo-prueba_propiedad', 'Desbloqueó el celular con su huella')
            elena.click('#entrega button[type=submit]')
            elena.wait_for_selector('#entrega .alerta-error')
            revisar('Un código incorrecto se rechaza y descuenta intentos', 'Quedan 4' in elena.text_content('#entrega .alerta-error'))
            elena.fill('#campo-codigo', codigo)
            elena.click('#entrega button[type=submit]')
            elena.wait_for_selector('#panel-datos .alerta-exito')
            revisar('La entrega queda registrada con su acta', 'Carné verificado' in elena.text_content('#panel-datos'))
            captura(elena, '13_entregado')

            beto.goto(f'{BASE}/mis-reclamaciones.html')
            beto.wait_for_selector('#lista-reclamaciones article')
            revisar('Beto ve su reclamación como entregada', 'Entregada' in beto.text_content('#lista-reclamaciones'))
            beto.goto(f'{BASE}/detalle-objeto.html?id={perdido_id}')
            beto.wait_for_selector('#panel-datos .insignia')
            revisar('Su reporte de pérdida quedó como recuperado', 'Recuperado' in beto.text_content('#panel-datos'))

            # --- Administración: auditoría y estadísticas ------------------------
            admin.goto(f'{BASE}/panel-admin.html')
            admin.wait_for_selector('#tabla-encargados tr')
            revisar('El panel muestra el trabajo de la encargada', 'Elena' in admin.text_content('#tabla-encargados'))
            captura(admin, '14_panel_admin')
            admin.goto(f'{BASE}/admin-auditoria.html?tabla=entregas')
            admin.wait_for_selector('#cuerpo-tabla tr td strong')
            revisar('La auditoría registró la entrega y quién la hizo', 'Elena' in admin.text_content('#cuerpo-tabla'))
            admin.goto(f'{BASE}/admin-auditoria.html?tabla=objetos&registro_id={encontrado_id}')
            admin.wait_for_selector('#cuerpo-tabla tr td strong')
            texto_auditoria = admin.text_content('#cuerpo-tabla')
            revisar('La auditoría del objeto muestra cada paso con su autor', 'Ana' in texto_auditoria and 'Elena' in texto_auditoria)
            captura(admin, '15_auditoria')
            admin.goto(f'{BASE}/admin-catalogos.html')
            admin.wait_for_selector('#tabla-parametros tr')
            captura(admin, '16_catalogos')

            # --- Separación de roles en la interfaz -------------------------------
            beto.goto(f'{BASE}/panel-admin.html')
            beto.wait_for_url('**/panel-estudiante.html')
            revisar('Un estudiante que abre el panel de admin vuelve a su panel', 'panel-estudiante' in beto.url)
            elena.goto(f'{BASE}/buscar-objetos.html')
            elena.wait_for_url('**/panel-encargado.html')
            revisar('Una encargada no entra a las pantallas de estudiante', 'panel-encargado' in elena.url)

            # --- XSS: el texto de un usuario nunca se interpreta como HTML ---------
            dialogos = []
            ana.on('dialog', lambda d: dialogos.append(d.message))
            xss_id = reportar(ana, 'perdido', '<img src=x onerror=alert(1)>', 'Prueba de seguridad con HTML en el nombre del objeto')
            ana.goto(f'{BASE}/detalle-objeto.html?id={xss_id}')
            ana.wait_for_selector('#titulo-objeto')
            revisar('Un nombre con HTML se muestra como texto', ana.text_content('#titulo-objeto') == '<img src=x onerror=alert(1)>')
            revisar('Y no ejecuta JavaScript', not dialogos and ana.locator('main img[src=x]').count() == 0)

            # --- Vista móvil ---------------------------------------------------------
            movil = nueva_pagina(navegador, 'móvil', movil=True)
            movil.goto(f'{BASE}/')
            movil.click('.boton-menu-movil')
            revisar('En el celular, el botón abre el menú', movil.locator('#menu-principal.abierto').count() == 1)
            captura(movil, '17_inicio_movil')

            revisar(f'Sin errores de JavaScript ni de CSP en el navegador ({len(ERRORES_NAVEGADOR)})', not ERRORES_NAVEGADOR)
            for error in ERRORES_NAVEGADOR:
                print('   ', error)
            print(f'    (respuestas 4xx esperadas y manejadas por la interfaz: {len(RESPUESTAS_ESPERADAS)})')
            for respuesta in RESPUESTAS_ESPERADAS:
                print('     -', respuesta)
            navegador.close()
    finally:
        servidor.terminate()
        servidor.wait(timeout=10)

    total = len(FALLOS)
    print(f"\n{'TODO CORRECTO' if not total else f'{total} verificación(es) fallaron'} · capturas en {CARPETA_CAPTURAS}")
    sys.exit(1 if total else 0)


if __name__ == '__main__':
    main()
