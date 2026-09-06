"""Pruebas unitarias de app/services/auth_service.py (sin Flask, sin BD)."""

from app.services import auth_service


def test_validar_contrasena_debil():
    errores = auth_service.validar_contrasena('12345678')
    assert len(errores) > 0


def test_validar_contrasena_fuerte():
    errores = auth_service.validar_contrasena('MiClave$Segura2026')
    assert errores == []


def test_validar_contrasena_comun_rechazada():
    errores = auth_service.validar_contrasena('Password123')
    assert any('común' in e or 'especial' in e for e in errores)


def test_validar_contrasena_no_debe_contener_el_correo():
    errores = auth_service.validar_contrasena('juanperez1234!A', correo='juanperez@sanmateo.edu.co')
    assert any('correo' in e for e in errores)


def test_correo_valido():
    assert auth_service.correo_valido('usuario@sanmateo.edu.co') is True


def test_correo_invalido():
    assert auth_service.correo_valido('no-es-un-correo') is False


def test_hash_no_es_texto_plano():
    hash_generado = auth_service.crear_hash('MiClave$Segura2026')
    assert hash_generado != 'MiClave$Segura2026'
    assert hash_generado.startswith('$argon2id$')


def test_verificar_password_correcta():
    hash_generado = auth_service.crear_hash('MiClave$Segura2026')
    assert auth_service.verificar_password('MiClave$Segura2026', hash_generado) is True


def test_verificar_password_incorrecta():
    hash_generado = auth_service.crear_hash('MiClave$Segura2026')
    assert auth_service.verificar_password('OtraClave$2027', hash_generado) is False
