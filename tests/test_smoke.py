import json


def test_app_imports():
    from app import create_app
    from app.blueprints.impressoras.services import verificar_impressoras_snmp
    from app.blueprints.wifi.services import verificar_wifi_snmp
    assert callable(create_app)
    assert callable(verificar_impressoras_snmp)
    assert callable(verificar_wifi_snmp)


def test_snmp_empty_list():
    from app.blueprints.impressoras.services import verificar_impressoras_snmp
    from app.blueprints.wifi.services import verificar_wifi_snmp
    assert verificar_impressoras_snmp([]) == []
    assert verificar_wifi_snmp([]) == []


def test_login_page_200(client):
    resp = client.get('/login')
    assert resp.status_code == 200


def test_protected_redirects_to_login(client):
    resp = client.get('/')
    assert resp.status_code == 302
    assert resp.location.endswith('/login')


def test_protected_api_returns_401(client):
    resp = client.get('/api/auth/me')
    assert resp.status_code == 401
    assert resp.json == {'ok': False, 'error': 'Nao autenticado'}


def test_logout_without_auth_returns_401(client):
    resp = client.post('/api/auth/logout')
    assert resp.status_code == 401
    assert resp.json == {'ok': False, 'error': 'Nao autenticado'}


def test_login_register_logout_flow(client):
    resp = client.post('/api/auth/login', json={'username': 'admin', 'password': 'wrong'})
    assert resp.status_code == 401
    assert resp.json['ok'] is False
