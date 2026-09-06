# EncuentraU

Plataforma universitaria para gestionar objetos perdidos y encontrados.

Versión actual: **v0.25 — Rediseño visual + autenticación segura + backend Python Flask**

Ver `ARCHITECTURE.md` para la arquitectura general, `SECURITY.md` para el
detalle de seguridad, y `CHANGELOG.md` para el historial de versiones.

## Cómo ejecutar el backend (Flask, oficial desde v0.25)

Requiere Python 3.10+.

```bash
cd backend
python -m venv venv
source venv/bin/activate      # En Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # y edita SECRET_KEY con un valor propio
python app.py
```

El servidor quedará disponible en `http://127.0.0.1:5000`.

## Cómo ver el frontend

El frontend sigue siendo HTML, CSS y JS puro (sin instalación), pero ahora
el login, registro y recuperación de contraseña hacen peticiones reales al
backend Flask, así que **necesitas tener el backend corriendo** para
probarlos.

Como usa cookies de sesión, es mejor no abrir el HTML con doble clic
(`file://`) sino servirlo con un servidor local sencillo, por ejemplo:

```bash
cd frontend/public
python -m http.server 5500
```

Y abrir `http://127.0.0.1:5500` en el navegador. El resto de páginas
(reportes, búsqueda, paneles) siguen usando datos simulados en
`js/datos-temporales.js`, sin conexión real todavía.
