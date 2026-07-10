import requests as _requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE = 'https://{}:8443'
SITE = 'default'

class UnifiError(Exception):
    pass

class UnifiController:
    def __init__(self, host, username, password):
        self.base = BASE.format(host)
        self.session = _requests.Session()
        self.session.verify = False
        self._login(username, password)

    def _login(self, username, password):
        r = self.session.post(f'{self.base}/api/login', json={
            'username': username, 'password': password
        }, timeout=10)
        if r.status_code != 200:
            raise UnifiError(f'Falha no login: HTTP {r.status_code}')

    def get_devices(self):
        r = self.session.get(f'{self.base}/api/s/{SITE}/stat/device', timeout=15)
        if r.status_code != 200:
            raise UnifiError(f'Falha ao buscar devices: HTTP {r.status_code}')
        data = r.json()
        devices = []
        for d in data.get('data', []):
            if d.get('type', '').lower() in ('uap', 'ap'):
                n2 = n5 = n6 = 0
                for vap in d.get('vap_table', []):
                    band = vap.get('radio', '')
                    sta = vap.get('num_sta', 0) or 0
                    if band == 'ng':
                        n2 += sta
                    elif band == 'na':
                        n5 += sta
                    elif band in ('6e', '6g'):
                        n6 += sta
                devices.append({
                    'name': d.get('name') or d.get('device_id', ''),
                    'model': d.get('model', ''),
                    'ip': d.get('ip', ''),
                    'num_sta': d.get('num_sta', 0),
                    'clientes_2g': n2,
                    'clientes_5g': n5,
                    'clientes_6g': n6,
                    'state': d.get('state', 0),
                    'mac': d.get('mac', ''),
                    'version': d.get('version', ''),
                    'uplink': d.get('uplink', {}),
                })
        return devices

    def get_clients_count(self):
        devices = self.get_devices()
        return {d['mac']: d['num_sta'] for d in devices}, devices

def testar_conexao(host, username, password):
    try:
        ctrl = UnifiController(host, username, password)
        devices = ctrl.get_devices()
        return True, f'Conectado! {len(devices)} APs encontrados.'
    except Exception as e:
        return False, str(e)
