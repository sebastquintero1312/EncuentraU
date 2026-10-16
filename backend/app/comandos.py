# Comandos de terminal (flask <comando>). Se ejecutan en el servidor, nunca
# por HTTP: son operaciones de confianza que no deben existir en la web.
#
#   flask crear-admin correo@sanmateo.edu.co
#   flask verificar-correo correo@sanmateo.edu.co
#   flask vencer-reservas
#
# Lo que hacen queda en la auditoría con usuario "Sistema".

from datetime import datetime, timezone

import click

from app.extensions import db


def registrar_comandos(app):

    @app.cli.command('crear-admin')
    @click.argument('correo')
    def crear_admin(correo):
        """Promueve a administrador a un usuario ya registrado y verificado.
        No existe ninguna forma de volverse administrador desde la web."""
        from app.models.usuario import ROL_ADMINISTRADOR, buscar_por_correo

        usuario = buscar_por_correo(correo)
        if not usuario:
            click.echo(f'No existe ningún usuario con el correo {correo}. Debe registrarse primero desde la web.')
            return
        if not usuario.correo_verificado:
            click.echo('Ese usuario todavía no verificó su correo. Verifícalo primero '
                       '(enlace del correo o "flask verificar-correo").')
            return
        usuario.rol = ROL_ADMINISTRADOR
        db.session.commit()
        click.echo(f'Usuario {usuario.correo} promovido a administrador correctamente.')

    @app.cli.command('verificar-correo')
    @click.argument('correo')
    def verificar_correo(correo):
        """Marca como verificado el correo de un usuario. Útil en desarrollo, o
        si el correo de verificación no llega y la oficina confirmó la
        identidad de la persona en persona."""
        from app.models.usuario import buscar_por_correo

        usuario = buscar_por_correo(correo)
        if not usuario:
            click.echo(f'No existe ningún usuario con el correo {correo}.')
            return
        if usuario.correo_verificado:
            click.echo('Ese correo ya estaba verificado.')
            return
        usuario.correo_verificado_en = datetime.now(timezone.utc)
        db.session.commit()
        click.echo(f'Correo {usuario.correo} verificado.')

    @app.cli.command('vencer-reservas')
    def vencer_reservas():
        """Libera los objetos cuyas reservas vencieron (se puede programar
        con cron; la aplicación también lo hace sola al abrir las pantallas)."""
        from app.services.oficina_service import vencer_reservas as vencer

        cantidad = vencer()
        click.echo(f'Reservas vencidas liberadas: {cantidad}')
