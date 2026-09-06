"""Verificación de extremo a extremo con un navegador real (Playwright).

A diferencia del resto de tests/ (que usan el test client de Flask), este
script maneja un Chromium real y hace clic/escribe como lo haría una
persona, contra un servidor Flask real corriendo en localhost. Sirve para
detectar bugs que pytest con el test client no puede ver: errores de
JavaScript, elementos mal referenciados, CSP bloqueando algo, etc.

Requisitos:
  1. El servidor debe estar corriendo: `python app.py` (con una base de
     datos limpia, para que los correos de prueba no choquen con datos
     previos).
  2. Playwright instalado: `pip install playwright && playwright install chromium`
     (incluido en requirements-dev.txt).

Uso:
    python tests/e2e/verificacion_navegador.py [URL_BASE]

Si no se indica URL_BASE, usa http://127.0.0.1:5000.

No es parte de la suite de `pytest` (no se ejecuta en cada `pytest tests/`)
porque requiere un servidor real corriendo aparte; es una herramienta de
verificación manual/CI adicional. Ver docs/evidencia/e2e_navegador_v1.0.txt
para la última ejecución registrada.
"""

import os
import subprocess
import sys

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
FALLOS = []


def revisar(nombre, condicion):
    estado = "OK" if condicion else "FALLO"
    print(f"[{estado}] {nombre}")
    if not condicion:
        FALLOS.append(nombre)


def escuchar_errores_consola(pagina, etiqueta):
    pagina.on("console", lambda m: revisar(f"Sin errores de consola ({etiqueta}: {m.text})", False) if m.type == "error" else None)
    pagina.on("pageerror", lambda exc: revisar(f"Sin errores de página ({etiqueta}: {exc})", False))


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()

        # ---------------- Ciudadano A: registro, reporte, mis-reportes ----------------
        a = browser.new_context().new_page()
        escuchar_errores_consola(a, "usuario A")

        a.goto(f"{BASE}/")
        revisar("La página de inicio carga en el mismo origen que la API", a.title() == "EncuentraU - Inicio")

        a.goto(f"{BASE}/registro.html")
        a.fill("#primerNombre", "Laura")
        a.fill("#primerApellido", "Gomez")
        a.fill("#correo", "laura.verificacion@sanmateo.edu.co")
        a.fill("#contrasena", "ClaveSegura!2026")
        a.fill("#confirmar", "ClaveSegura!2026")
        a.click("#btn-registro")
        a.wait_for_url("**/login.html", timeout=5000)

        a.fill("#correo", "laura.verificacion@sanmateo.edu.co")
        a.fill("#contrasena", "ClaveSegura!2026")
        a.click("#btn-login")
        a.wait_for_url("**/panel-ciudadano.html", timeout=5000)
        revisar("Login redirige al panel y saluda por nombre real", "Laura" in a.text_content("#saludo"))

        a.goto(f"{BASE}/reportar-perdido.html")
        a.fill("#nombreObjeto", "Mochila azul Totto Verif")
        a.select_option("#categoria", "Accesorios")
        a.fill("#descripcion", "Mochila azul con laptop adentro, verificación E2E")
        a.fill("#ubicacion", "Biblioteca central")
        a.fill("#fecha", "2026-09-01")
        a.click("#form-reporte button[type=submit]")
        a.wait_for_selector("#mensaje-confirmacion.visible", timeout=5000)
        revisar("El reporte de objeto perdido se guarda de verdad (backend real)", True)

        a.goto(f"{BASE}/mis-reportes.html")
        a.wait_for_selector("#cuerpo-tabla tr")
        revisar("Mis reportes muestra el reporte recién creado", "Mochila azul Totto Verif" in a.text_content("#cuerpo-tabla"))

        # ---------------- Ciudadano B: reporte encontrado, búsqueda, coincidencia, solicitud ----------------
        b = browser.new_context().new_page()
        escuchar_errores_consola(b, "usuario B")

        b.goto(f"{BASE}/registro.html")
        b.fill("#primerNombre", "Carlos")
        b.fill("#primerApellido", "Ruiz")
        b.fill("#correo", "carlos.verificacion@sanmateo.edu.co")
        b.fill("#contrasena", "OtraClaveSegura!26")
        b.fill("#confirmar", "OtraClaveSegura!26")
        b.click("#btn-registro")
        b.wait_for_url("**/login.html", timeout=5000)
        b.fill("#correo", "carlos.verificacion@sanmateo.edu.co")
        b.fill("#contrasena", "OtraClaveSegura!26")
        b.click("#btn-login")
        b.wait_for_url("**/panel-ciudadano.html", timeout=5000)

        b.goto(f"{BASE}/reportar-encontrado.html")
        b.fill("#nombreObjeto", "Mochila azul encontrada Verif")
        b.select_option("#categoria", "Accesorios")
        b.fill("#descripcion", "Encontré una mochila azul Totto con laptop, verificación E2E")
        b.fill("#ubicacion", "Biblioteca central")
        b.fill("#fecha", "2026-09-02")
        b.click("#form-reporte button[type=submit]")
        b.wait_for_selector("#mensaje-confirmacion.visible", timeout=5000)

        b.goto(f"{BASE}/buscar-objetos.html")
        b.fill("#texto", "Totto Verif")
        b.click("#btn-buscar")
        b.wait_for_timeout(500)
        revisar("La búsqueda real (backend) encuentra el reporte de Laura", "Mochila azul Totto Verif" in b.text_content("#resultados"))

        b.click("#resultados >> text=Mochila azul Totto Verif >> xpath=ancestor::div[@class='card'] >> text=Ver detalle")
        b.wait_for_selector("#detalle h2")
        revisar("El motor de coincidencias sugiere el reporte de Carlos como posible pareja", "Posibles coincidencias" in b.text_content("#detalle"))

        b.click("text=Solicitar recuperación")
        b.wait_for_selector("#form-solicitud")
        b.fill("#contacto", "carlos.verificacion@sanmateo.edu.co")
        b.fill("#mensaje", "Esa mochila es mía, tiene un cuaderno rojo de Cálculo adentro")
        b.click("#form-solicitud button[type=submit]")
        b.wait_for_selector("#mensaje-confirmacion.visible", timeout=5000)
        revisar("La solicitud de reclamación se envía correctamente", True)

        a.goto(f"{BASE}/mis-reportes.html")
        a.click("#cuerpo-tabla a:has-text('Ver detalle')")
        a.wait_for_selector("#detalle h2")
        detalle_laura = a.text_content("#detalle")
        revisar("El dueño ve la información privada de verificación de la solicitud", "cuaderno rojo" in detalle_laura)
        revisar("El reporte pasa a 'en proceso' al recibir una solicitud", "en proceso" in detalle_laura)

        # Un tercero (no dueño, no admin) NO debe poder ver esa información
        c = browser.new_context().new_page()
        respuesta_id = a.url.split("id=")[-1]
        resp = c.request.get(f"{BASE}/api/objetos/{respuesta_id}/solicitudes")
        revisar("Un desconocido no autenticado no puede ver las solicitudes privadas (401)", resp.status == 401)

        # ---------------- Administrador: panel, gestión de reportes/solicitudes/usuarios ----------------
        admin = browser.new_context().new_page()
        escuchar_errores_consola(admin, "admin")

        admin.goto(f"{BASE}/registro.html")
        admin.fill("#primerNombre", "Root")
        admin.fill("#primerApellido", "EncuentraU")
        admin.fill("#correo", "root.verificacion@sanmateo.edu.co")
        admin.fill("#contrasena", "Segura!Panel2026")
        admin.fill("#confirmar", "Segura!Panel2026")
        admin.click("#btn-registro")
        admin.wait_for_url("**/login.html", timeout=5000)

        # Promoción real a administrador, vía el mismo CLI de servidor que se
        # documenta en README.md (nunca por HTTP: no existe endpoint para esto).
        directorio_backend = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        entorno = dict(os.environ, FLASK_APP="app.py")
        subprocess.run(
            [sys.executable, "-m", "flask", "crear-admin", "root.verificacion@sanmateo.edu.co"],
            cwd=directorio_backend, env=entorno, check=True,
        )

        admin.fill("#correo", "root.verificacion@sanmateo.edu.co")
        admin.fill("#contrasena", "Segura!Panel2026")
        admin.click("#btn-login")
        admin.wait_for_url("**/panel-admin.html", timeout=5000)
        revisar("Login de un administrador redirige a panel-admin (no panel-ciudadano)", True)

        admin.goto(f"{BASE}/gestion-solicitudes.html")
        admin.wait_for_selector(".card")
        revisar("La solicitud de Carlos aparece en gestión de solicitudes", "carlos.verificacion@sanmateo.edu.co" in admin.text_content("#lista-solicitudes"))

        admin.on("dialog", lambda d: d.accept("Verificado"))
        admin.click("button:has-text('Aprobar')")
        admin.wait_for_timeout(800)
        revisar("Aprobar una solicitud desde el panel funciona", "aprobada" in admin.text_content("#lista-solicitudes"))

        objeto_tras_aprobar = admin.request.get(f"{BASE}/api/objetos/{respuesta_id}").json()
        revisar("El reporte reclamado pasa a 'resuelto' tras la aprobación", objeto_tras_aprobar["objeto"]["estado"] == "resuelto")

        browser.close()

    print("\n" + "=" * 60)
    if FALLOS:
        print(f"RESULTADO: {len(FALLOS)} verificación(es) fallaron:")
        for f in FALLOS:
            print(" -", f)
        sys.exit(1)
    else:
        print("RESULTADO: todas las verificaciones pasaron.")


if __name__ == "__main__":
    main()
